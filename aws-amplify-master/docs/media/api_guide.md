# API

AWS Amplify API module provides a simple solution when making HTTP requests. It provides an automatic, lightweight signing process which complies with [AWS Signature Version 4](http://docs.aws.amazon.com/general/latest/gr/signature-version-4.html). 

* [Installation and Configuration](#installation-and-configuration)
  - [Automated Setup](#automated-setup)
  - [Manual Setup](#manual-setup)
* [Integration](#integration)
  * [GET](#get)
  * [POST](#post)
  * [PUT](#put)
  * [DELETE](#delete)
  * [HEAD](#head)

## Installation and Configuration

Please refer to this [Guide](install_n_config.md) for general setup. Here are Analytics specific setup.

The API module can be used out of the box for signed requests against Amazon API Gateway when the API Authorization is set to **AWS_IAM**. 

You are required to pass in an Amazon Cognito Identity Pool ID, allowing the library to retrieve base credentials for a user even in an UnAuthenticated state. AWS Amplify also requires a list of your APIs, comprised of a friendly name for the API and the endpoint URL. 

Amazon Cognito Identity Pool requires to have access to the API using Amazon IAM. You can configure it by yourself or let [AWS Mobile Hub do it for you](#automated-setup)!

[Amazon API Gateway](http://docs.aws.amazon.com/apigateway/latest/developerguide/getting-started.html)

### Automated Setup

To create a project fully functioning with the API category.

```
$ npm install -g awsmobile-cli
$ cd my-app
$ awsmobile init
$ awsmobile enable cloud-api
$ awsmobile push
```

In your project i.e. App.js:

```
import Amplify, { API } from 'aws-amplify';
import aws_exports from './aws-exports';
Amplify.configure(aws_exports);
```

### Manual Setup

After configuring this resources you can add these lines to your source code.
```js
import Amplify, { API } from 'aws-amplify';

Amplify.configure({
    Auth: {
    // REQUIRED - Amazon Cognito Identity Pool ID
        identityPoolId: 'XX-XXXX-X:XXXXXXXX-XXXX-1234-abcd-1234567890ab',
    // REQUIRED - Amazon Cognito Region
        region: 'XX-XXXX-X', 
    // OPTIONAL - Amazon Cognito User Pool ID
        userPoolId: 'XX-XXXX-X_abcd1234', 
    // OPTIONAL - Amazon Cognito Web Client ID
        userPoolWebClientId: 'XX-XXXX-X_abcd1234',
    },
    API: {
        endpoints: [
            {
                name: "MyAPIGatewayAPI",
                endpoint: "https://1234567890-abcdefgh.amazonaws.com"
            },
            {
                name: "MyCustomCloudFrontApi",
                endpoint: "https://api.my-custom-cloudfront-domain.com",

            },
            {
                name: "MyCustomLambdaApi",
                endpoint: "https://lambda.us-east-1.amazonaws.com/2015-03-31/functions/yourFuncName/invocations",
                service: "lambda",
                region: "us-east-1"
            }
        ]
    }
});

```

### Service Endpoints

While it is best practice to utilize something like Amazon API Gateway for Rest APIs for both security, scalability and management, you can also utilize most AWS APIs by passing in the service information to the configuration for an endpoint. For a list of service endpoints see [here](https://docs.aws.amazon.com/general/latest/gr/rande.html). For more details related to API Gateway Invoke specifically, see [here](https://docs.aws.amazon.com/lambda/latest/dg/API_Invoke.html).

For example, you can utilize a custom domain directly with a Lambda function by setting up an Amazon Cloudfront origin pointing to (change the region to your relevent region): 
https://lambda.us-east-1.amazonaws.com

This post explains more in depth how to setup the Amazon Cloudfront distribution:
https://forum.serverless.com/t/directly-proxying-lambda-via-cloudfront-without-api-gateway/3808

 NOTE: In order to call these service endpoints you will need to be sure your Amazon Cognito role is configured with appropriate access to that service. See [here](https://docs.aws.amazon.com/cognito/latest/developerguide/iam-roles.html) for more details.

## Integration

First note the name of the API that you want to invoke. If you manually configured the API, you most likely already know the API name. If you use Automated Setup or configure your API on AWS Mobile Hub you can check the API name in the Mobile Hub console by clicking Cloud Logic tile. 

The below code assumes use of the Automated Setup.

Each method of Amplify's API module returns a Promise which is seen in the below examples with different HTTP verbs. Configure the `apiName`, `path` and `headers` according to your settings.

Note: To get the full response from API call, set ```response``` to ```true``` in the ```init``` object.

### **GET**

```js
let apiName = 'MyApiName';
let path = '/path'; 
let myInit = { // OPTIONAL
    headers: {} // OPTIONAL
    response: true // OPTIONAL (return entire response object instead of response.data)
}
API.get(apiName, path, myInit).then(response => {
    // Add your code here
});

```

Example with async/await

```js
async function getData() { 
    let apiName = 'MyApiName';
    let path = '/path';
    let myInit = { // OPTIONAL
        headers: {} // OPTIONAL
    }
    return await API.get(apiName, path, myInit);
}

getData();
```
### Note about headers

To use custom headers on your HTTP request you need to add these to Amazon API Gateway first. For more info about configuring headers go [here](http://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-cors.html)

If you used one click import or AWS Mobile Hub to create your API, you can do the following:

1. Go to your project on AWS Mobile Hub console.
2. Go to resources and click the link on Amazon API Gateway section. This will redirect you to Amazon API Gateway console.
3. On Amazon API Gateway console, click on the path you want to configure (e.g. /{proxy+})
4. Then click the Actions dropdown and select **Enable CORS**
5. Add your custom header (e.g. my-custom-header) on the text field Access-Control-Allow-Headers, separated by commas, like so: 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,my-custom-header'
6. Click on 'Enable CORS and replace existing CORS headers' and confirm.
7. Finally, similar to step 3, click the Actions dropdown and then **Deploy API**. Select **Development** on deployment stage and then **Deploy**. (Deployment could take a couple of minutes).

### **POST**

```js
let apiName = 'MyApiName'; // replace this with your api name.
let path = '/path'; //replace this with the path you have configured on your API
let myInit = {
    body: {}, // replace this with attributes you need
    headers: {} // OPTIONAL
}

API.post(apiName, path, myInit).then(response => {
    // Add your code here
});

```

Example with async/await

```js
async function postData() { 
    let apiName = 'MyApiName';
    let path = '/path';
    let myInit = { // OPTIONAL
        body: {}, // replace this with attributes you need
        headers: {} // OPTIONAL
    }
    return await API.post(apiName, path, myInit);
}

postData();
```

### **PUT**

```js
let apiName = 'MyApiName'; // replace this with your api name.
let path = '/path'; // replace this with the path you have configured on your API
let myInit = {
    body: {}, // replace this with attributes you need
    headers: {} // OPTIONAL
}

API.put(apiName, path, myInit).then(response => {
    // Add your code here
});

```

Example with async/await

```js
async function putData() { 
    let apiName = 'MyApiName';
    let path = '/path';
    let myInit = { // OPTIONAL
        body: {}, // replace this with attributes you need
        headers: {} // OPTIONAL
    }
    return await API.put(apiName, path, myInit);
}

putData();
```

### **DELETE**

```js
let apiName = 'MyApiName'; // replace this with your api name.
let path = '/path'; //replace this with the path you have configured on your API
let myInit = { // OPTIONAL
    headers: {} // OPTIONAL
}

API.del(apiName, path, myInit).then(response => {
    // Add your code here
});

```

Example with async/await

```js
async function deleteData() { 
    let apiName = 'MyApiName';
    let path = '/path';
    let myInit = { // OPTIONAL
        headers: {} // OPTIONAL
    }
    return await API.delete(apiName, path, myInit);
}

deleteData();
```

### **HEAD**

```js
let apiName = 'MyApiName'; // replace this with your api name.
let path = '/path'; //replace this with the path you have configured on your API
let myInit = { // OPTIONAL
    headers: {} // OPTIONAL
}
API.head(apiName, path, myInit).then(response => {
    // Add your code here
});

```

Example with async/await

```js
async function head() { 
    let apiName = 'MyApiName';
    let path = '/path';
    let myInit = { // OPTIONAL
        headers: {} // OPTIONAL
    }
    return await API.head(apiName, path, myInit);
}

head();
```
