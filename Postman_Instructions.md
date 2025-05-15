# [Postman Instructions](https://www.guru99.com/postman-tutorial.html)

To run the postman tests, you will need to either install the Postman extension on VSCode or use Postman from their [website](https://www.postman.com/). I believe you need an account for either option.

The instructions to follow for either option are essentially identical, as I understand it, due to the format for both being identical.

![image of postman](https://www.guru99.com/images/1/011119_1057_PostmanTuto7.png)

## Create a Collection to Store the Requests
You will first want to create a collection to store the requests.

**(VSCode)**: Click the **+** button in the top left corner.

**(Postman Website)**: Click the **+** button in the top left corner and then clicking **New Collection**.

**(Optional)**: You may also create collections within other collections, essentially being subfolders. This is useful for organizing related routes, but not required.

## Create a Request
After creating the collection, you will want to create a new request. 

**(VSCode)**: Hover over the collection you want to store teh request within. Click on the three dots next to its name and click **Add Request**.

**(Postman Website)**: Click the **+** button in the top left corner.

## Fill in the Request Information

![postman request image](https://www.guru99.com/images/1/011119_1057_PostmanTuto10.png)

After creating the request, you will want to fill in the information. There are three important sections to be concerned with:
1. **The request method**: This is the type of method that will be used for the url. Usually these will be **`GET`**, **`POST`**, **`PATCH`**, or **`DELETE`**.
2. **The request url**: This is the url that will be used for the request. The url will correspond to the route that you want to test.
3. **The request body**: This is the body that will be sent with the request. This is usually a **`form-data`** or **`JSON`** object.

Routes/Endpoints are how the frontend and the backend of an application communicate with each other. They are the way that the frontend can call the backend to perform certain actions.

The combinantion of the request method and the request url is what is used to call the corresponding route on the backend.

Postman sort of simulates the frontend calling the backend.

A good way to think about it is that it's essentially like calling a function. The url and method combination are like the function name, and the body is like the arguments that you would pass to the function.

I have provided the request methods and routes that you will need to use in the [README.md](README.md) file, so you should hopefully not need to worry about these two, though I'll still give a bit of a brief description anyway.

The most important thing you'll probably need to worry about is the request body.

### The Request Method
Usually, the method will be one of the following, depending on the desired outcome:
- **`GET`**: This is used when the desired outcome is to retrieve information.
- **`POST`**: This is used to send information to the server.
- **`PATCH`**: This is used to update information on the server.
- **`DELETE`**: This is used to delete information from the server.

You can select the method by clicking on the dropdown menu next to the request url. **(Marked 1)**

### The Request URL
The url is the route that you want to call. The parts of the backend that you are actually intended to call have corresponding route that you use to call them. 

You can type in the url in the box next to the request method. **(Marked 2)**

The url will be in the format of **`localhost:5000/<route>`**. The route will be the route that you want to test.

### The Request Body
The request body is the information that you want to send to the backend. There are a few different types of body type that you can pick, but the two main ones I use are **`form-data`** and **`raw`** with a **`JSON`** format.

You can select the body type by selecting the **`Body`** tab underneath the request url. **(Marked 3)**

After selecting the **`Body`** tab, you can select the body type by selecting one of the bubbles next to the different body types.

In the [README.md](README.md) file, the body keys that you will use for each route have been provided.

#### Form Data
To select form data, select the **`form-data`** bubble.

For form data, there are two colums: 
* **`Key`**: The name of the field.
* **`Value`**. The value that will be read from the field.

You can add a new entry simply by entering the name of the key in the **`Key`** column and the value of the field in the **`Value`** column. A new, empty entry will appear underneath after one of these is filled.

You do not need to specify the type of the value or add quotes. The backend will handle that.

#### Raw JSON
To select raw JSON, select the **`raw`** bubble. After you do this, a dropdown menu should appear next to the different bubble options. Select **`JSON`** from the dropdown menu.

For raw JSON, you will need to enter the JSON object in the box. The JSON object will be in the format of **`{ "key": "value" }`**.

## Saving the Request
After you create the request, you can save it and the information will be saved so you can run it again.

## Running the Request
To run the request, click the **`Send`** button to the right of the url. This should send the request to the backend and the response will be displayed in the response section.

I have found there are times that the output displayed doesn't update after running the request. If this occurs, I recommend clicking on the **`Cookies`** tab and then clicking back on the **`Body`** tab.



# [Instruction from Guru99.com](https://www.guru99.com/postman-tutorial.html)

For a more in-depth look at how to use Postman, I have linked the tutorial that I initally used to learn how to use it. As well, I have included the image and labels if this is more helpful to you.

![image of postman](https://www.guru99.com/images/1/011119_1057_PostmanTuto7.png)

1. **New** – This is where you will create a new request, collection or environment.
2. **Import** – This is used to import a collection or environment. There are options such as import from file, folder, link or paste raw text.
3. **Runner** – Automation tests can be executed through the Collection Runner. This will be discussed further in the next lesson.
4. **Open New** – Open a new tab, Postman Window or Runner Window by clicking this button.
5. **My Workspace** – You can create a new workspace individually or as a team.
6. **Invite** – Collaborate on a workspace by inviting team members.
7. **History** – Past requests that you have sent will be displayed in History. This makes it easy to track actions that you have done.
8. **Collections** – Organize your test suite by creating collections. Each collection may have subfolders and multiple requests. A request or folder can also be duplicated as well.
9. **Request tab** – This displays the title of the request you are working on. By default, “Untitled Request” would be displayed for requests without titles.
10. **HTTP Request** – Clicking this would display a dropdown list of different requests such as GET, POST, COPY, DELETE, etc. In Postman API testing, the most commonly used requests are GET and POST.
11. **Request URL** – Also known as an endpoint, this is where you will identify the link to where the API will communicate with.
12. **Save** – If there are changes to a request, clicking save is a must so that new changes will not be lost or overwritten.
13. **Params** – This is where you will write parameters needed for a request such as key values.
14. **Authorization** – In order to access APIs, proper authorization is needed. It may be in the form of a username and password, bearer token, etc.
15. **Headers** – You can set headers such as content type JSON depending on the needs of the organization.
16. **Body** – This is where one can customize details in a request commonly used in POST request.
17. **Pre-request Script** – These are scripts that will be executed before the request. Usually, pre-request scripts for the setting environment are used to ensure that tests will be run in the correct environment.
18. **Tests** – These are scripts executed during the request. It is important to have tests as it sets up checkpoints to verify if response status is ok, retrieved data is as expected and other tests.