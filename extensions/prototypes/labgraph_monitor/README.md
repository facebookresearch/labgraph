# LabGraph Monitor

LabGraph Monitor helps visualize the graph built. In order to run the application, you will need to first set it up using React using the below steps:

In case you do not have npm installed, follow the below steps to get started:

Download Node.js from [here](https://nodejs.org/en/download/) 

Once Node is installed, you can verify that node/npm was installed successfully by running the following: 

```
node -v
npm -v
```

The above should display the version of node/npm that were installed. For example:

```
6.14.13
```

Now that you have npm installed, you can create a new React application using the terminal. Navigate to the folder where you want the application to be installed and run the below code to create a new React application. We are going to call the application "labgraph_monitor_extension" for the sake of this example but feel free to choose another name. 

Note: npx is a package that comes with npm 5.2+ 
```
npx create-react-app labgraph_monitor_extension
```

Next, you will need to install the dagre library and ReactFlow that help in layouting the graph. 
Run the code below to install them
```
npm i dagre
```

```
npm install --save react-flow-renderer
```

Once the application is created, we will need to change and add some files to get the LabGraph Monitor working. 

First, you can validate that everything is going well so far by running the new sample React app in your browser. Navigate using the terminal to the labgraph_monitor_extension folder and run

```
npm start
```

This should open a sample React app in your localhost and display the React icon. 

Now that we have the initial application set up, we can start adding the new files. 

Add the App.js, helper.js and App.css files downloaded from [labgraph repo](https://github.com/facebookresearch/labgraph) found at .\labgraph\extensions\prototypes\labgraph_monitor\src to your labgraph_monitor_extension application. You need to add them in the ./labgraph_monitor_extension/src folder 

You can now navigate to your localhost in browser again to see the changes. As the backend server is not running yet, you will see a blank white page. 

Note: incase you closed your react app while downloading other libraries, you will need to start it again by navigating to the labgraph_monitor_extension and running:

```
npm start
```

With that, LabGraph Monitor is ready! Before you see the graph displayed in your browser, you will need to start the backend server. 