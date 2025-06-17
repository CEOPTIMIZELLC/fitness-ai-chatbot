import numpy as np
from flask import current_app

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from scipy.cluster.hierarchy import linkage, fcluster

from config import distance_threshold

class Data_Clustering:
    # Step 1: Get embeddings from OpenAI
    def _get_embeddings(self, df, name_column):
        # Get embeddings for all exercises
        exercises = df[name_column].tolist()
        embed = OpenAIEmbeddings(model=current_app.config["EMBEDDING_MODEL"])
        embeddings = embed.embed_documents(exercises)
        df['embedding'] = embeddings
        return df
    
    # Make sure embeddings are numpy arrays
    def _retrieve_embedding_matrix(self, df):
        embedding_matrix = np.vstack(df["embedding"].values)
        return embedding_matrix

    def _cluster_df_by_embeddings(self, df):
        if 'embedding' not in df.columns:
            print("No embeddings present")
            return None

        embedding_matrix = self._retrieve_embedding_matrix(df)

        # Compute linkage matrix
        Z = linkage(embedding_matrix, method="ward")  # 'ward' works well for embeddings

        # Example: cut dendrogram at distance threshold t
        df["General Cluster"] = fcluster(Z, t=distance_threshold, criterion="distance")
        return df

    # Generate the name for the individual cluster of items.
    def _generate_cluster_name(self, items, structured_output_class, system):
        item_names = ", ".join(f'"{s}"' for s in items)

        human = """Given the following list of item names:
    {item_names}

    What is a concise, general category name that best describes this group of items?
    """.format(item_names=item_names)

        check_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", human),
            ]
        )

        llm = ChatOpenAI(model=current_app.config["LANGUAGE_MODEL"])
        structured_llm = llm.with_structured_output(structured_output_class)
        item_classifier = check_prompt | structured_llm
        general_item_name = item_classifier.invoke({})
        return general_item_name.name

    # Generate the names for all of the clusters.
    def _generate_cluster_names(self, df, name_column, structured_output_class, system_message):
        clustered_items = df.groupby("General Cluster")[name_column].apply(list).to_dict()
        cluster_names = {}

        for cluster_id, items in clustered_items.items():
            name = self._generate_cluster_name(items, structured_output_class, system_message)
            cluster_names[cluster_id] = name

        df["General "+name_column] = df["General Cluster"].map(cluster_names)
        return df
    
    # Perform semantic embedding, hierarchal clustering, and general name generation for the dataframe.
    def _cluster_main(self, df, name_column, structured_output_class, system_message=""):
        self._get_embeddings(df, name_column)
        self._cluster_df_by_embeddings(df)
        self._generate_cluster_names(df, name_column, structured_output_class, system_message)
        return None

