from config import generate_cluster_names, db_max_workers
from logging_config import LogDBInit
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import numpy as np
from flask import current_app

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from scipy.cluster.hierarchy import linkage, fcluster

from config import distance_threshold

base_system_message = """You are a helpful assistant trained in item classification and terminology.

You have been provided a list of items that belong to a singular group and have been tasked with generating a name for the general item that all of these fall under.

"""

base_human_message = """Given the following list of item names:
{item_names}

What is a concise, general category name that best describes this group of items?
"""

from pydantic import BaseModel, Field
class GeneralItems(BaseModel):
    """Information to extract."""
    name: str = Field(description="The name of the general item that all of the other items are variations of.")
    reasoning: str = Field(description="The reasoning behind the choice of name based on the items in the group.")


class Data_Clustering:
    def __init__(self, df, name_column, structured_output_class=None, system_message=None, human_message=None):
        self.df = df
        self.name_column = name_column
        self.cluster_name_column = "General " + name_column
        self.structured_output_class = structured_output_class if structured_output_class else GeneralItems
        self.system = system_message if system_message else base_system_message
        self.human = human_message if human_message else base_human_message
        return None

    # Step 1: Get embeddings from OpenAI
    def _get_embeddings(self):
        LogDBInit.clustering(f"Getting embeddings.")
        # Get embeddings for all items
        items = self.df[self.name_column].tolist()
        embed = OpenAIEmbeddings(model=current_app.config["EMBEDDING_MODEL"])
        embeddings = embed.embed_documents(items)
        self.df['embedding'] = embeddings
        return None

    # Retrieve the generated embeddings as a numpy arrays
    def _retrieve_embedding_matrix(self):
        LogDBInit.clustering(f"Retrieving embedding matrix as a numpy matrix.")
        embedding_matrix = np.vstack(self.df["embedding"].values)
        return embedding_matrix

    # Perform the clustering algorithm on the items based on the embeddings.
    def _cluster_df_by_embeddings(self, embedding_matrix):
        LogDBInit.clustering(f"Performing clustering algorithm on items.")
        # Compute linkage matrix
        Z = linkage(embedding_matrix, method="ward")  # 'ward' works well for embeddings

        # Example: cut dendrogram at distance threshold t
        self.df["General Cluster"] = fcluster(Z, t=distance_threshold, criterion="distance")
        return None

    # Generate the name for the individual cluster of items.
    def _generate_cluster_name(self, language_model, items):
        item_names = ", ".join(f'"{s}"' for s in items)
        check_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system),
                ("human", self.human.format(item_names=item_names)),
            ]
        )

        llm = ChatOpenAI(model=language_model)
        structured_llm = llm.with_structured_output(self.structured_output_class)
        item_classifier = check_prompt | structured_llm
        general_item_name = item_classifier.invoke({})
        return general_item_name.name
    
    # Generate the names for all of the clusters.
    def _generate_cluster_names(self, clustered_items):
        LogDBInit.clustering(f"Generating cluster names.")
        cluster_names = {}

        language_model=current_app.config["LANGUAGE_MODEL"]

        with ThreadPoolExecutor(max_workers=db_max_workers) as ex:
            futures = {
                ex.submit(
                    self._generate_cluster_name, 
                    language_model, items
                ): cluster_id
                for cluster_id, items in clustered_items.items()
            }

            # Wrap your items in tqdm to get a progress bar
            for fut in tqdm(as_completed(futures), total=len(futures), desc="Processing clusters"):
                cluster_id = futures[fut]
                name = fut.result()
                cluster_names[cluster_id] = name
        return cluster_names

    # Create the default names for all of the clusters.
    def _default_cluster_names(self, clustered_items):
        LogDBInit.clustering(f"Adding default cluster names.")
        cluster_names = {}
        for cluster_id, items in clustered_items.items():
            name = self._generate_cluster_name(items)
            cluster_names[cluster_id] = name
        return cluster_names

    # Generate the names for all of the clusters.
    def _add_cluster_names(self):
        clustered_items = self.df.groupby("General Cluster")[self.name_column].apply(list).to_dict()

        # Generate names in parallel.
        if generate_cluster_names:
            cluster_names = self._generate_cluster_names(clustered_items)

        # Placeholder names if names shouldn't be generated.
        else:
            cluster_names = self._default_cluster_names(clustered_items)

        self.df[self.cluster_name_column] = self.df["General Cluster"].map(cluster_names)
        return None

    # Perform semantic embedding, hierarchal clustering, and general name generation for the dataframe.
    def run(self):
        self._get_embeddings()
        
        # Check that embeddings were made before executing.
        if 'embedding' not in self.df.columns:
            LogDBInit.data_errors("No embeddings present")
            return None
        
        embedding_matrix = self._retrieve_embedding_matrix()
        self._cluster_df_by_embeddings(embedding_matrix)

        self._add_cluster_names()
        return None

def Main(df, name_column, structured_output_class=None, system_message=None, human_message=None):
    data_clustering = Data_Clustering(
        df=df, 
        name_column=name_column, 
        structured_output_class=structured_output_class, 
        system_message=system_message, 
        human_message=human_message
    )
    data_clustering.run()

    return data_clustering.df