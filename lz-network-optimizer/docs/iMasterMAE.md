<img src="./r0owcee5.png"
style="width:8.26319in;height:5.15972in" />

**MAE-Access** **V100R021C10**

**Open** **API** **Developer** **Guide** **(Wireless** **Network)**

**Issue** **01**

**Date** **2021-08-26**

<img src="./dhrsutt2.png"
style="width:1.02847in;height:1.00208in" />**HUAWEI** **TECHNOLOGIES**
**CO.,** **LTD.**

> **Copyright** **©** **Huawei** **Technologies** **Co.,** **Ltd.**
> **2021.** **All** **rights** **reserved.**
>
> No part of this document may be reproduced or transmitted in any form
> or by any means without prior written consent of Huawei Technologies
> Co., Ltd.
>
> **Trademarks** **and** **Permissions**
>
> <img src="./3ua4p24v.png"
> style="width:0.32153in;height:0.31181in" />and other Huawei trademarks
> are trademarks of Huawei Technologies Co., Ltd.
>
> All other trademarks and trade names mentioned in this document are
> the property of their respective holders.
>
> **Notice**
>
> The purchased products, services and features are stipulated by the
> contract made between Huawei and the customer. All or part of the
> products, services and features described in this document may not be
> within the purchase scope or the usage scope. Unless otherwise
> specified in the contract, all statements, information, and
> recommendations in this document are provided "AS IS" without
> warranties, guarantees or representations of any kind, either express
> or implied.
>
> The information in this document is subject to change without notice.
> Every effort has been made in the preparation of this document to
> ensure accuracy of the contents, but all statements, information, and
> recommendations in this document do not constitute a warranty of any
> kind, express or implied.
>
> Huawei Technologies Co., Ltd.
>
> Address:
>
> Website:
>
> Email:

Huawei Industrial Base Bantian, Longgang Shenzhen 518129 People's
Republic of China

https://www.huawei.com

support@huawei.com

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. i

> MAE-Access
>
> Open API Developer Guide (Wireless Network) Contents
>
> **Contents**

**1** **About** **This**
**Document..................................................................................................................1**

**2** **Open**
**APIs.......................................................................................................................................2**
2.1 Introduction to
OpenAPIs............................................................................................................................................2
2.2 Introduction to
REST....................................................................................................................................................2
2.3 Introduction to
JSON....................................................................................................................................................3
2.4 API Communication
Protocols.....................................................................................................................................3

**3** **API** **Architecture** **and**
**Functions.................................................................................................4**

**4** **API** **Interconnection**
**Process.......................................................................................................5**
4.1 Preparing for the Interconnection
.................................................................................................................................5
4.2 Creating a Third-Party User on the
OSS.......................................................................................................................5
4.3 (Optional) Deploying iSStar
Scripts.............................................................................................................................6
4.4 Verifying the Interconnection
.......................................................................................................................................7

**5** **API**
**List..........................................................................................................................................10**
5.1 List of Public
APIs......................................................................................................................................................10
5.1.1 LoginAPI
................................................................................................................................................................10
5.2 List of
MMLAPIs.......................................................................................................................................................13
5.2.1 Issuing a Single MML
Command............................................................................................................................13
5.2.1.1 Format of MML NE Response
Messages.............................................................................................................16
5.2.2 Issuing an MML Batch Script Task
.........................................................................................................................20
5.2.2.1 Creating a Task
.....................................................................................................................................................20
5.2.2.2 Querying Task Status Based on the Task
ID.........................................................................................................23
5.2.2.3 Downloading the Task Execution Result Based on the Task
ID...........................................................................25
5.2.2.4 Deleting a Task Based on the Task ID
..................................................................................................................29
5.3 List ofAlarmAPIs for
FM..........................................................................................................................................31
5.3.1 Querying
Alarms......................................................................................................................................................31
5.4 List of Performance APIs for PM
...............................................................................................................................39
5.4.1 Creating a Performance Data Query
Task................................................................................................................39
5.4.2 Obtaining Performance
Data....................................................................................................................................45
5.4.3 Deleting a Performance Result Query
Task.............................................................................................................50
5.5 API for Querying Topology Cell Information
............................................................................................................52
5.6 List of iSStar
APIs......................................................................................................................................................56

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. ii
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) Contents

5.6.1 Creating iSStar Task
................................................................................................................................................56
5.6.2 Querying iSStar
Tasks..............................................................................................................................................61
5.6.3 Deleting iSStar
Tasks...............................................................................................................................................64
5.6.4 Downloading the iSStar Task Result
Report............................................................................................................66
5.7 List of System InformationAPIs
................................................................................................................................68
5.7.1 Testing MAE Northbound
Connectivity..................................................................................................................68
5.7.2 Querying the OMC Number of
MAE......................................................................................................................69
5.7.3 Querying the Current MAE Version
........................................................................................................................71

**6** **Error** **Code**
**List.............................................................................................................................73**

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. iii

MAE-Access

Open API Developer Guide (Wireless Network) 1 About This Document

> **1** **About** **This** **Document** **Purpose**
>
> An open API is a REST-based open interface provided by the MAE NBI
> system. REST is short for Representational State Transfer. Third-party
> developers can use open APIs to access open MAE resources, including
> alarm, performance, and MML modules.
>
> **Product** **Version**

||
||
||
||

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 1

> MAE-Access
>
> Open API Developer Guide (Wireless Network) 2 OpenAPIs
>
> **2** **Open** **APIs** 2.1 Introduction to Open APIs
>
> 2.2 Introduction to REST
>
> 2.3 Introduction to JSON
>
> 2.4 API Communication Protocols

**2.1** **Introduction** **to** **Open** **APIs**

> Open APIs use open authentication. An asymmetric encryption technology
> is used to authenticate users, obtain resources, and implement data
> sharing among platforms, enterprises, and entities. Open APIs are
> common applications at service-oriented websites. A website service
> provider encapsulates its website services in a series ofAPIs and
> enables the APIs for third-party developers. This is called APIs for
> opening websites (open APIs for short).
>
> Open APIs provide a standard integration solution that facilitates
> quick integration of third-party systems. Open APIs can be used only
> through HTTPS upon authorization. This
>
> increases security. Data is exchanged in JavaScript object notation
> (JSON) format to simplify data read and write as well as to reduce the
> volume of consumed traffic in comparison with the XML format.

**2.2** **Introduction** **to** **REST**

> Representational State Transfer (REST) is a design and development
> method for network applications. It decreases development complexity
> and improves system scalability. The design concepts and principles of
> this architecture style are as follows:
>
> 1\. All entities on a network can be abstracted as resources.
>
> 2\. Each resource has a unique resource identifier, and operations on
> resources do not change the resource identifiers.
>
> 3\. All operations are stateless.
>
> 4\. Four standard methods are used to operate resources: POST, GET,
> PUT, and DELETE. − POST is used to create a resource.
>
> − GET is used to query resource information.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 2
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 2 OpenAPIs
>
> − PUT is used to update a resource.
>
> − DELETE is used to delete a resource.

**2.3** **Introduction** **to** **JSON**

> JSON is a lightweight, standard data format. JSON strings are more
> concise than XML, thus occupying less space and decreasing network
> traffic. JSON has the following two structures:
>
>  Object: Braces ({}) hold objects, for example, {key1: value1, key2:
> value2, ...}. You can access data using Object.key.
>
>  Array: Brackets (\[\]) hold arrays, for example, \[element1,
> element2, ...\]. You can access data using Object\[index\]. The index
> starts from 0.
>
> The following code shows how to obtain JSON strings.
>
> { "id":"00000002",
>
> "href":"/api/rest/configurationManagement/v1/bulkCM/exportJobs/00000002",
> "userName":"testuser",
> "exportPath":"/export/home/omc/var/fileint/cm/0/",
> "reportPath":"/export/home/omc/var/fileint/cm/0/report",
>
> "errorInfo":"" }

**2.4** **API** **Communication** **Protocols**

> AllAPIs for the NBI system are HTTPS-based RESTfulAPIs.
>
> HyperText Transfer Protocol (HTTP) is one of the most widely used
> network protocols in Internet.
>
> HTTP is designed to provide a method of releasing and receiving HTML
> pages.
>
> Resources requested according to HTTP or Hypertext Transfer Protocol
> over Secure Sockets Layer (HTTPS) are identified by their Uniform
> Resource Identifiers (URIs).
>
> Hypertext Transfer Protocol over Secure Socket Layer (HTTPS) is a
> secure HTTP channel. HTTPS is designed based on SSL. Therefore, data
> is encrypted using SSL to ensure data transmission security.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 3

MAE-Access<img src="./eecrdhty.png"
style="width:5.10555in;height:2.58333in" />

Open API Developer Guide (Wireless Network) 3 API Architecture and
Functions

> **3** **API** **Architecture** **and** **Functions**
>
> Each service releases some interfaces through northbound open APIs for
> third-party systems to call.

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 4

> MAE-Access
>
> Open API Developer Guide (Wireless Network) 4 API Interconnection
> Process
>
> **4** **API** **Interconnection** **Process** 4.1 Preparing for the
> Interconnection
>
> 4.2 Creating a Third-Party User on the OSS
>
> 4.3 (Optional) Deploying iSStar Scripts
>
> 4.4 Verifying the Interconnection

**4.1** **Preparing** **for** **the** **Interconnection**

> You need to obtain the following information before the
> interconnection.

||
||
||
||
||

**4.2** **Creating** **a** **Third-Party** **User** **on** **the**
**OSS**

**Creating** **a** **User**

> Before calling APIs, the OSS needs to create users and bind roles to
> the users.
>
> For information related to user creation, see the user management
> sections in the product documentation. The process of creating a user
> is as follows.
>
> **Step** **1** Log in to MAE.
>
> Open a web browser, enter **https://***MAE* *IP* *address***:31943/**
> (for example, **https://\*.\*.\*.\*:31943/**) in the address box, and
> press **Enter**.
>
> **Step** **2** Creating a User
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 5
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 4 API Interconnection
> Process
>
> 1\. On the main menu, choose **Common** \> **Security** \> **User**
> **Management** \> **Users**. On the displayed page, click **Create**.
>
> 2\. Set **Type** to **Third-party**, set user information, and click
> **Next**. 3. In the role list, select **NBI** **User** **Group** and
> click **Next**.
>
> 4\. Click **OK**.
>
> **Step** **3** (Optional) If the MML interface needs to be called,
> grant the MML permission to the user.
>
> In the **Apps** area of the MAE home page, click **Access** to enter
> the MAE-Access home page. On the main menu, choose **Security** \>
> **NE** **User** **Management**. In the navigation pane, choose
> **MMLCommand** **Group** **Manager**. Select the user created in Step
> 2 based on the user type, grant MML command groups to the user based
> on the NE types contained in the managed objects, and click **Apply**.
>
> **----End**

**4.3** **(Optional)** **Deploying** **iSStar** **Scripts** **Step**
**1** Develop iSStar script applications.

> 1\. Scripts are in .hsp3 format. You can choose **MAE** \> **Access**
> \> **Maintenance** \> **iSStar** \> **Development** **Platform** to
> develop .hsp3 scripts or choose **Application** **Platform** \>
> **Application** **Management** to download the developed applications.
>
> 2\. To ensure security and reliability, do not access scripts outside
> the .hsp3 package in the .hsp3 script. For example, do not use the
> Call, Import, and CreateTask functions to invoke scripts outside the
> .hsp3 package.
>
> 3\. Operations on multiple NEs in a single task are executed in
> sequence. Therefore, you are not advised to perform time-consuming
> operations on each NE when a large number of NEs are involved.
>
> **Step** **2** Use SFTP or FTPS to upload the script application to
> the MAE master service node.
>
> Use FileZilla to upload the **test.hsp3** application to the
> **/home/sopuser** directory on the MAE master service node as the
> **sopuser** user.
>
> **Step** **3** Create a directory on the MAE server.
>
> 1\. Create a script repository.
>
> Use PuTTY to log in to the MAE master service node as the **sopuser**
> user in SSH mode. Create a folder in the
> **/export/home/sysm/ftproot/** directory for storing scripts.
>
> **\$** **su** **ossuser**
>
> **\$** **cd** **/export/home/sysm/ftproot/** **\$** **mkdir**
> **iSStarScriptStore**
>
> **\$** **chmod** **770** **iSStarScriptStore** 2. Create a task script
> directory.
>
> Create the required directory in the **iSStarScriptStore** directory
> based on service scenarios and task types. The RESTFul interface for
> creating tasks needs to transfer the directory name as a parameter to
> the RESTFul server.
>
> For example, a task directory can be created by running the following
> commands: **\$** **cd**
> **/export/home/sysm/ftproot/iSStarScriptStore**
>
> **\$** **mkdir** ***demo***
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 6
>
> MAE-Access<img src="./5co0rhqt.png"
> style="width:0.75208in;height:0.26319in" />
>
> Open API Developer Guide (Wireless Network)
>
> **\$** **chmod** **770** ***demo***
>
> **\$** **cp** **/home/sopuser/*test.hsp3*** **\$** **cd** ***demo***
>
> **\$** **chmod** **770** ***test.hsp3***
>
> 4 API Interconnection Process

**/export/home/sysm/ftproot/iSStarScriptStore/*demo*/**

> **Step** **4** Check the files that have been uploaded to the MAE
> server.
>
> Use PuTTY to log in to the MAE master service node as the **sopuser**
> user in SSH mode.
>
> Run the following commands to obtain the sha256 verification value of
> the file.
>
> **\$** **su** **ossuser**
>
> **\$** **cd** **/export/home/sysm/ftproot/iSStarScriptStore/*demo***
>
> **\$** **sha256sum**
> **/export/home/sysm/ftproot/iSStarScriptStore/*demo*/*test.hsp3***
>
> **----End**
>
> 1\. **To** **call** **iSStarAPIs,** **you** **need** **to** **deploy**
> **iSStar** **scripts.**
>
> 2\. **In** **this** **document,** ***demo*** **and** ***test.hsp3***
> **are** **used** **as** **examples.** **Replace** **them** **as**
> **required.**

**4.4** **Verifying** **the** **Interconnection**

**Debugging** **APIs** **Using** **Postman**

> This section uses the Chrome web browser as an example to describe how
> to use Postman to debug an API.
>
> **Prerequisites**
>
> You have obtained the required IP address and port number. For
> details, see 4.1 Preparing for the Interconnection.
>
> You have created a northbound login authentication user. For details,
> see 4.2 Creating a Third-Party User on the OSS.
>
> **Obtaining** **the** **Token**
>
> **Step** **1** Start Postman, and enter the following URL in the
> address box:
>
> **https://*Primary*** ***IP*** ***address*** ***of*** ***the***
> ***application*** ***plane*** ***in*** ***the*** ***MAE***
> ***system*:31127/api/rest/securityManagement/v1/oauth/token**
>
> **Step** **2** Set the request header parameters.
>
> **Content-Type:** **application/json**
>
> **Accept:** **application/json**
>
> **Step** **3** Set the request body parameters.
>
> **The** **request** **type** **is** **PUT.** **The** **body**
> **parameters** **are** **as** **follows:**
>
> **{**
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 7

MAE-Access<img src="./c2ia35ye.png"
style="width:0.75208in;height:0.26319in" /><img src="./nai3t0y3.png"
style="width:0.75208in;height:0.26389in" /><img src="./nohti2sd.png"
style="width:0.75208in;height:0.26319in" />

Open API Developer Guide (Wireless Network) 4 API Interconnection
Process

> **"grantType":** **"password",**
>
> **"userName":** **"",**
>
> **"value":** **""**
>
> **}**
>
> 1\. **You** **need** **to** **switch** **the** **request** **body**
> **parameters** **to** **the** **raw** **mode.**
>
> 1\. **You** **need** **to** **replace** **userName** **and** **value**
> **with** **the** **user** **name** **and** **password** **of** **the**
> **user** **for** **NBI** **system** **login** **authentication.**
>
> **Step** **4** Send the URI. If status code 200 is returned, the
> request is successful.
>
> **Step** **5** View the response.
>
> **{**
>
> **"accessSession":**
>
> **"x-c97tk99iarc6kbo5hhjz09bw2n6rdeo76r08ukjw9gvxpders4ikjt5iqo0a05tgk805lfpcpeb**
> **wlf7vbvvthcuoimle6obz49lcli4bbspc2len9evsalk8sant9hhc",**
>
> **"roaRand":** **"5ac18de46d9a7b72d3ea5ad7877ff6d566a2a24b2078f48e",**
>
> **"expires":** **1800,**
>
> **"additionalInfo":** **null**
>
> **}**
>
> accessSession indicates the returned token.
>
> When calling an API, you need to fill the value of accessSession in
> the X-Auth-Token field. The following is an example:
>
> **X-Auth-Token:x-c97tk99iarc6kbo5hhjz09bw2n6rdeo76r08ukjw9gvxpders4ikjt5iqo0a05tgk805lfpc**
> **pebwlf7vbvvthcuoimle6obz49lcli4bbspc2len9evsalk8sant9hhc**
>
> **----End**
>
> **Calling** **a** **Northbound** **API** **(Example)**
>
> **Step** **1** In the Postman app, enter an URI in POST mode.
>
> **https://***Primary* *IP* *address* *of* *the* *application* *plane*
> *in* *the* *MAE*
> *system***:31127/api/rest/performanceManagement/v1/measurementResults**
>
> **Step** **2** Set the request header parameters.
>
> Content-Type:application/json
>
> X-Auth-Token:x-c97tk99iarc6kbo5hhjz09bw2n6rdeo76r08ukjw9gvxpders4ikjt5iqo0a05tgk80
> 5lfpcpebwlf7vbvvthcuoimle6obz49lcli4bbspc2len9evsalk8sant9hhc
>
> **The** **value** **of** **X-Auth-Token** **is** **the** **value**
> **of** **accessSession** **obtained** **in** **"Obtaining** **the**
> **Token."**
>
> **Step** **3** Set the request body parameters.
>
> {

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 8

MAE-Access

Open API Developer Guide (Wireless Network) 4 API Interconnection
Process

> "\*\*\*":"\*\*\*\*\*\*\*\*\*"
>
> }
>
> **Step** **4** Send the URI. If status code 200 is returned, the API
> is successfully called.
>
> {
>
> "\*\*\*":"\*\*\*\*\*\*\*\*\*"
>
> }
>
> **----End**

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 9

> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> **5** **API** **List** 5.1 List of Public APIs
>
> 5.2 List of MMLAPIs
>
> 5.3 List ofAlarmAPIs for FM
>
> 5.4 List of Performance APIs for PM
>
> 5.5 API for Querying Topology Cell Information
>
> 5.6 List of iSStarAPIs
>
> 5.7 List of System Information APIs

**5.1** **List** **of** **Public** **APIs** **5.1.1** **Login** **API**

**Function**

> ThisAPI is used for logging in to MAE using the name and password of a
> user account. A session ID that uniquely identifies the login session
> is returned after a successful login.

**Precautions**

> 
>
> 
>
> 

If the logged-in user has not performed any operations within 30
minutes, the session ID automatically becomes invalid by default.

You need to create users and bind roles to the user for interconnecting
with third-party systems.

If the password is entered incorrectly for five consecutive times, the
user account will be locked. In this case, you need to manually unlock
the user account on the OSS.

**Call** **Method**

> PUT
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 10
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**URI**

> /api/rest/securityManagement/v1/oauth/token

**Request** **Parameters**

> **Table** **5-1** Header parameter list

||
||
||
||

> **Table** **5-2** Bodyparameter list

||
||
||
||

> **Table** **5-3** Parameters in theTokenRequest MO

||
||
||
||
||
||

**Sample** **Request** PUT

> /api/rest/securityManagement/v1/oauth/token Host: 10.10.10.10:31127
>
> Content-Type: application/json Accept: application/json
> Accept-Language: en-US
>
> {
>
> "grantType": "password", "userName": "test", "value": "Changeme_123"
>
> }
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 11
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**Response** **Parameters**

> If the returned status code is **200**, the login is successful.
>
> **Table** **5-4** Bodyparameter list

||
||
||
||

> **Table** **5-5** Parameters in theTokenResponse MO

||
||
||
||
||
||
||

> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Date: Wed,21 Nov 2018 10:00:00 GMT Server: example-server
>
> Content-Type: application/json {
>
> "accessSession":
>
> "x-o5gb05o8eo1fapgb49lj7wfsuqbytgvxry7w0ahds9lic59dpdqnnuga9f9gnuldg8mko7bxtigauma
> rlfeltis8arhjioqlk8lecb891i5ctcbtemjxnt3x6nqr8asb",
>
> "roaRand": "58a68cd75382dd55189d0b855463fc2370b994bfdbfead27",
> "expires": 1800,
>
> "additionalInfo": null }
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 12
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**Operation** **Severity**

> Minor

**5.2** **List** **of** **MML** **APIs**

**5.2.1** **Issuing** **a** **Single** **MML** **Command**

**Function**

> The function allows you to issue an MML command to the specified NEs.
> You can specify multiple NE names at a time.

**Precautions**

> 
>
> 
>
> 
>
> 
>
> 
>
> 
>
> 
>
> 

Each specified NE name must be unique.

If the number of specified NE names exceeds 100, you are advised to use
a script. The timeout period for requesting the bus is 5 minutes. If
there are too many NEs, the request may time out.

The single-command issuance API displays only messages returned in
synchronous mode. For asynchronous commands such as data
synchronization, download, and version activation commands, the
single-command issuance API does not return progress and result messages
reported by NEs in asynchronous mode. If such query mode is used, you
can issue the script to the NE.

The maximum size of the request body is 2 MB. The maximum size of a
response message is 10 MB.

A maximum of 15 concurrent requests are supported.

For the MML commands that need to run for a long time or whose response
messages are large, you are advised to run them in MML batch script task
issuing mode.

If multiple NE names that are specified include incorrect name, an error
is reported.

**Call** **Method**

> POST

**URI**

> /api/rest/mmlManagement/v1/command

**Request** **Parameters**

> **Table** **5-6** Header parameter list

||
||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 13
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||
||

> **Table** **5-7** Bodyparameter list

||
||
||
||

> **Table** **5-8** Parameters in the CommandInfo MO

||
||
||
||
||

**Sample** **Request**

> POST /api/rest/mmlManagement/v1/command Host: serverIP:port
>
> Content-Type: application/json; charset=UTF-8 X-Auth-Token:
>
> x-jupj3v47dfhf4bpjnyermo2k9jpftdmmfveqgbmppf2kjwgaikfwo5rskbjulisbbwk89ghcqovwruar
> ftlefvanfy5ctes9hehi2mfyoa5grzmk9fldhcft07g52rka
>
> Content-Length:… {
>
> "command": "LST VER:;", "neNames": \["pml","pTest"\]
>
> }
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 14
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**Response** **Parameters**

> If the returned status code is **200**, the operation is successful.
>
> **Table** **5-9** Bodyparameter list

||
||
||
||
||
||
||

> **Table** **5-10** Parameters in the Result MO

||
||
||
||
||
||
||
||

> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 15
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> If the returned status code is **500**, the server is abnormal. For
> details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Content-Type: application/json; charset=UTF-8 Content-Length:…
>
> {
>
> "asynchId": "0301_20210302193828_303", "results": \[{
>
> "name": "pml",
>
> "report": "+++ LTE 2021-03-02 19:38:47\r\nO&M
> \#2440\r\n%%/\*1879048219\*/LST VER:;%%\r\nRETCODE = 0 Operation
> succeeded.\r\n\r\nResult of current software
>
> query\r\n--------------------------------\r\n Current Software Version
> = BTS1 V111222\r\n Current SoftwareStatus = Normal\r\n Current Hot
> Patch Version = V111222\r\n\r\n(Number of results = 1)\r\n\r\nDetail
>
> information\r\n------------------\r\nApplication Type Application
> Version Software Version Application Hot Patch Version Software Hot
> Patch Version\r\n\r\neNodeB LTEV200R007C00SPC110 BTS1 V111222 V111222
> BTS1 V111222\r\n(Number of results = 1)\r\n\r\n\r\n--- END\r\n\r\n",
>
> "result": "Operation succeeded.", "retCode": 0,
>
> "serialId": -1 },
>
> {
>
> "name": "pTest",
>
> "report": "+++ LTE 2021-03-02 19:38:47\r\nO&M
> \#2440\r\n%%/\*1879048219\*/LST VER:;%%\r\nRETCODE = 0 Operation
> succeeded.\r\n\r\nResult of current software
>
> query\r\n--------------------------------\r\n Current Software Version
> = BTS1 V111222\r\n Current Software Status = Normal\r\n Current Hot
> Patch Version = V111222\r\n\r\n(Number of results = 1)\r\n\r\nDetail
>
> information\r\n------------------\r\nApplication Type Application
> Version Software Version Application Hot Patch Version Software Hot
> Patch Version\r\n\r\neNodeB LTEV200R007C00SPC110 BTS1 V111222 V111222
> BTS1 V111222\r\n(Number of results = 1)\r\n\r\n\r\n--- END\r\n\r\n",
>
> "result": "Operation succeeded.", "retCode": 0,
>
> "serialId": -1 }
>
> \],
>
> "retCode": "90000",
>
> "retMessage": "Execution succeeded." }

**Operation** **Severity**

> Minor

**5.2.1.1** **Format** **of** **MML** **NE** **Response** **Messages**

> The response message body of an NE can be described in a horizontal
> list or a vertical list.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 16
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**Horizontal** **List**

> The horizontal list is widely used and applicable to the display of
> multiple returned records that are not separated by blank lines. For
> example, it is used to display multiple returned results in the
> following scenarios: querying all the subracks of a module, querying
> the status of all the boards in a subrack, collecting entity traffic
> statistics, or querying the test results.
>
> The format of a horizontal list is defined as follows:
>
> \<Attribute name 1'A0'Lw1\>\<2SP\>\<Attribute name
> 2'A0'Lw2\>\<2SP\>......\<2SP\>\<Attribute name *n*'A0'Lw*n*\>\r\n
>
> \r\n
>
> \<Attribute 1 Value 1'A0'Lw1\>\<2SP\>\<Attribute 2 Value
> 1'A0'Lw2\>\<2SP\>......\<2SP\>\<Attribute *n* Value 1'A0'Lw*n*\>\r\n
>
> \<Attribute 1 Value 2'A0'Lw1\>\<2SP\>\<Attribute 2 Value
> 2'A0'Lw2\>\<2SP\>......\<2SP\>\<Attribute *n* Value 2'A0'Lw*n*\>\r\n
>
> ... ...
>
> \<Attribute 1 Value *m*'A0'Lw1\>\<2SP\>\<Attribute 2 Value
> *m*'A0'Lw2\>\<2SP\>......\<2SP\>\<Attribute *n* Value
> *m*'A0'Lw*n*\>\r\n
>
> Note:
>
> 1\. Lw*n* indicates the width of the attribute in column *n*. The
> maximum width of the attribute in each column is determined based on
> the report requirements. The minimum width is six characters.
>
> 2\. The first line displays the attribute name of the output, which is
> separated from the following data area by a blank line.
>
> 3\. The attribute of each row is left-aligned.
>
> 4\. The attribute name and value cannot contain two or more
> consecutive spaces.
>
> 5\. In the horizontal list, if an attribute of a record does not have
> the corresponding attribute value, **NULL** is used to indicate the
> attribute value.

**Vertical** **List**

> The vertical list is applicable to the display of one or more returned
> records. Multiple returned records are separated by blank lines. For
> example, it is used to display returned results in the following
> scenarios: querying users or querying a test result.
>
> Rule description:
>
> 1\. In a vertical list, if each attribute has only one value, each row
> displays one attribute. The attribute name is on the left of the equal
> sign, and the value is on the right of the equal sign. The content on
> the left of the equal mark is right-aligned, and the content on the
> right of the equal mark is left-aligned. The format is as follows:
>
> \<0SP\>\<Attribute name 1\>\<2SP\>=\<2SP\>\<Value 1\>\r\n
> \<0SP\>\<Attribute name 2\>\<2SP\>=\<2SP\>\<Value 2\>\r\n
> \<0SP\>\<Attribute name 3\>\<2SP\>=\<2SP\>\<Value 3\>\r\n
> \<0SP\>\<Attribute name 4\>\<2SP\>=\<2SP\>\<Value 4\>\r\n
>
> 2\. In the vertical list, if an attribute does not have the
> corresponding attribute value, **NULL** is used to indicate the
> attribute value. The format is as follows:
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 17
>
> MAE-Access<img src="./xr0fel4k.png"
> style="width:4.56667in;height:4.45139in" />
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> \<0SP\>\<Attribute name\>\<2SP\>=\<2SP\>\<<u>NULL</u>\>\r\n
>
> 3\. In the vertical list, if an attribute has more than one value,
> each value is displayed in a line and the first value is used for left
> alignment. The format is as follows:
>
> \<0SP\>\<Attribute name 1\>\<2SP\>=\<2SP\>\<Value 1\>\r\n
>
> \<0SP\>\<Attribute name 2\>\<2SP\>=\<2SP\>\<Value 2.1\>\r\n
>
> =\<2SP\>\<Value 2.2\>\r\n
>
> =\<2SP\>\<Value 2.3\>\r\n
>
> ... ...
>
> =\<2SP\>\<Value 2.*x*\>\r\n
>
> \<0SP\>\<Attribute name 3\>\<2SP\>=\<2SP\>\<Value 3\>\r\n
>
> \<0SP\>\<Attribute name 4\>\<2SP\>=\<2SP\>\<Value 4\>\r\n
>
> Note: \< Value 2.*x*\> indicates the *x*th value of the second
> attribute.

**Message** **structure** **diagram**

> **Figure** **5-1** Horizontal list
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 18

MAE-Access<img src="./wgz3xoiq.png"
style="width:5.17708in;height:3.36667in" />

Open API Developer Guide (Wireless Network) 5 API List

> **Figure** **5-2** Vertical list
>
> Note:
>
> 1\. 2. 3. 4. 5. 6. 7. 8. 9. 10. 11. 12. 13. 14. 15. 16. 17.

Issue 01 (2021-08-26)

Start identifier

Source identifier (device name) Message creation date

Creation time Service report flag

Message sequence number MML commands

Return code Returned message

Title of the message entry Attribute name

Attribute value Message entry Record in the entry Result summary Overall
entry content End flag

> Copyright © Huawei Technologies Co., Ltd. 19
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**5.2.2** **Issuing** **an** **MML** **Batch** **Script** **Task**

**5.2.2.1** **Creating** **a** **Task**

**Function**

> This function allows you to create a script task based on the uploaded
> MML script file and the specified task name.

**Precautions**

> 
>
> 
>
> 
>
> 
>
> 
>
> 

The task name must be a string of 1 to 64 characters and be unique, and
cannot contain any character in \`~!@#\$%^&;\*()+{}\[\]\\':,.?\<\>".

The MML script file should be only in TXT format. The file content
should contain the commands and NE information.

The name of an MML script file cannot contain any character in
/\\\>\*?\|":'&.

The maximum size of the request body is 2 MB. Therefore, the size of the
MML script file cannot exceed 2 MB.

The script encryption password needs to be specified if the MML script
contains the password field. Otherwise, an error is reported.

New tasks cannot be created after the number of tasks reaches the
maximum. The maximum number of tasks depends on the number of MML
scripts on the **Task** **Management** page.

**Call** **Method**

> POST

**URI**

> /api/rest/mmlManagement/v1/tasks

**Request** **Parameters**

> **Table** **5-11** Header parameter list

||
||
||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 20
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> **Table** **5-12** List of form parameters

||
||
||
||

> **Table** **5-13** Parameters in theTaskRequest MO

||
||
||
||
||
||

**Scripts** **Description**

> The format of an MML script is as follows:
>
> *MML* *command*:*Parameters*; {*NE* *1*,*NE* *2*,,...} /\**Comment*\*/
>
> 1\. One line in the MML script contains only one MML command.
>
> 2\. MML command: parameter; is the command field, which cannot be
> empty. This field cannot contain the following characters: semicolon
> (;), two or more consecutive percent signs (%), two or more
> consecutive spaces, start characters of MML messages (+++), or end
> characters of MML messages (--- END).
>
> 3\. {NE 1,NE 2, and ...} indicates the target NEs and can be empty for
> non-CloudEdge NEs. If {} is used, {} must be filled with NE names. You
> can enter multiple NE names separated by commas (,) in single-byte
> character (SBC) case. The NE name cannot contain the following
> characters in the SBC case: comma (,), colon (:), semicolon (;), open
> brace ({), and close brace (}). For CloudEdge NEs, {NE 1,NE 2, and
> ...} indicates the target VNFC and must contain one VNFC name.
>
> 4\. /\*comment\*/ is the comment field and can be omitted. This field
> cannot contain the following characters: two or more consecutive
> percent signs (%), two or more consecutive spaces, start characters of
> MML messages (+++), or end characters of MML messages (--- END).
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 21
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> The following provides an example of a correct MML script:
>
> LST VER:; {HSS_1,HSS_2}
>
> DSP PATCH:OT=BOARDTYPE,BT=UMPT; {HSS_1}

**Sample** **Request**

> POST /api/rest/mmlManagement/v1/tasks HTTP/1.1 X-Auth-Token:
>
> x-c9di1hbutj7u9h46hg5fjzlf2p2lio3svuti6rfvdf1dtdlidcqkipiqdi5etiukde7u47s5dcbzo9g6
> 852ofujx5g1fapanhdemg6ftliftilvuti48jvoapglipc2l
>
> Host: \*.\*.\*.\*:31127
>
> Content-Type:
> multipart/form-data;boundary=------FormBoundaryShouldDifferAtRuntime
> ------FormBoundaryShouldDifferAtRuntime
>
> Content-Disposition: form-data; name="file"; filename="mml.txt";
> taskName="mmlTask" Content-Type: text/xml
>
> \[message-part-body; type: text/xml, size: 1924 bytes\]
> ------FormBoundaryShouldDifferAtRuntime--

**Response** **Parameters**

> If the returned status code is **200**, the operation is successful.
>
> **Table** **5-14** Bodyparameter list

||
||
||
||

> **Table** **5-15** Parameters in theTaskResponse MO

||
||
||
||
||
||

> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 22
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> If the returned status code is **500**, the server is abnormal. For
> details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Date: Wed,21 Nov 2018 10:00:00 GMT Server: example-server
>
> Content-Type: application/json {
>
> "taskId": "123" }

**Operation** **Severity**

> Minor

**5.2.2.2** **Querying** **Task** **Status** **Based** **on** **the**
**Task** **ID**

**Function**

> This function allows you to query the task status based on the
> returned task ID after an MML task is created successfully.

**Precautions**

>  To query the task status, you need to use the task ID returned when
> the task is created.

**Call** **Method**

> GET

**URI**

> /api/rest/mmlManagement/v1/tasks/{taskId}/status

**Request** **Parameters**

> **Table** **5-16** Header parameter list

||
||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 23
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> **Table** **5-17** Path parameter list

||
||
||
||

**Sample** **Request**

> GET /api/rest/mmlManagement/v1/tasks/123/status HTTP/1.1 X-Auth-Token:
>
> x-jupj3v47dfhf4bpjnyermo2k9jpftdmmfveqgbmppf2kjwgaikfwo5rskbjulisbbwk89ghcqovwruar
> ftlefvanfy5ctes9hehi2mfyoa5grzmk9fldhcft07g52rka
>
> Host: \*.\*.\*.\*:31127

**Response** **Parameters**

> If the returned status code is **200**, the operation is successful.
>
> **Table** **5-18** Bodyparameter list

||
||
||
||

> **Table** **5-19** Parameters in the StatusResponse MO

||
||
||
||
||
||
||

> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 24
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **404**, the requested resource does
> not exist or the URI is incorrect. For details, see the response
> message body.
>
> If the returned status code is **500**, the server is abnormal. For
> details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Content-Type:application/json {
>
> "progress": 100, "currentState": 3
>
> }

**Operation** **Severity**

> Minor

**5.2.2.3** **Downloading** **the** **Task** **Execution** **Result**
**Based** **on** **the** **Task** **ID**

**Function**

> This function allows you to download the result file of a task when
> the task is complete.

**Precautions**

> 
>
> 
>
> 
>
> 

The ID returned when the task is created needs to be used.

If the task does not exist or is not complete, an error is reported.

The maximum size of an MML result file is 500 MB. If the size of the
result file is less than 100 MB, the system returns a .txt file. If the
size of the result file is greater than 100 MB and less than 500 MB, the
system compresses the file in ZIP format and returns it.

It is recommended that a maximum of five file download requests be
executed at the same time.

**Call** **Method**

> GET

**URI**

> /api/rest/mmlManagement/v1/tasks/{taskId}/result

**Request** **Parameters**

> **Table** **5-20** Header parameter list

||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 25
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||

> **Table** **5-21** Path parameter list

||
||
||
||

**Sample** **Request**

> GET /api/rest/mmlManagement/v1/tasks/123/result HTTP/1.1 X-Auth-Token:
>
> x-jupj3v47dfhf4bpjnyermo2k9jpftdmmfveqgbmppf2kjwgaikfwo5rskbjulisbbwk89ghcqovwruar
> ftlefvanfy5ctes9hehi2mfyoa5grzmk9fldhcft07g52rka
>
> Host: \*.\*.\*.\*:31127

**Response** **Parameters**

> If the returned status code is **200**, the operation is successful.
>
> **Table** **5-22** Parameter list of successful transactions

||
||
||
||

> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 26

MAE-Access

Open API Developer Guide (Wireless Network) 5 API List

> If the returned status code is **404**, the requested resource does
> not exist or the URI is incorrect. For details, see the response
> message body.
>
> If the returned status code is **500**, the server is abnormal. For
> details, see the response message body.
>
> **Table** **5-23** Parameter list of failed transactions

||
||
||
||
||

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 27

> MAE-Access<img src="./h1vyv3i3.png"
> style="width:4.51042in;height:6.34306in" />
>
> Open API Developer Guide (Wireless Network) 5 API List

**Result** **File** **Format**

> **Figure** **5-3** Content of a task execution result file
>
> Note:
>
> 1\. 2. 3. 4. 5. 6.
>
> Issue 01 (2021-08-26)

Number of MML commands that are successfully executed Number of MML
commands that fail to be executed Details about failed MML commands

Details about succeeded MML commands MML command

NE name

> Copyright © Huawei Technologies Co., Ltd. 28
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> 7\. NE response message. For details about the message format, see
> 5.2.1.1 Format of MML NE Response Messages.

**Example** **of** **a** **Downloaded** **Result** **File** Script Task
: test ==========Summary========== Succeeded Number : 1

> Failed Number : 0 ===========================
>
> ==========Failed MML Command==========
> ======================================
>
> ==========Succeeded MML Command========== MML Command-----LST VER:;
>
> NE : by
>
> Report : +++ by 2021-03-02 19:38:47 O&M \#2440
>
> %%/\*1879048219\*/LST VER:;%% RETCODE = 0 Operation succeeded.
>
> Result of current software query --------------------------------
>
> Current Software Version = BTS1 V111222 Current Software Status =
> Normal Current Hot Patch Version = V111222
>
> (Number of results = 1)
>
> Detail information ------------------
>
> Application Type Application Version Software Version Application Hot
> Patch Version Software Hot Patch Version
>
> eNodeB V111222 BTS1 V111222 V111222 BTS1 V111222 (Number of results =
> 1)
>
> --- END
>
> ======================================

**Operation** **Severity**

> Minor

**5.2.2.4** **Deleting** **a** **Task** **Based** **on** **the**
**Task** **ID**

**Function**

> This function allows you to delete the task after the task result is
> downloaded to avoid the failure to create a new task due to too many
> tasks.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 29
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**Precautions**

> 
>
> 
>
> 

The ID returned when the task is created needs to be used. A running
task cannot be deleted.

After a task is executed and the task result is downloaded, this API is
called to delete the task to reduce system resource usage. If the task
is not deleted immediately, MAE automatically deletes the task that has
been created for more than two days.

**Call** **Method**

> DELETE

**URI**

> /api/rest/mmlManagement/v1/tasks/{taskId}

**Request** **Parameters**

> **Table** **5-24** Header parameter list

||
||
||
||

> **Table** **5-25** path parameters

||
||
||
||

**Sample** **Request**

> DELETE /api/rest/mmlManagement/v1/tasks/123 HTTP/1.1 X-Auth-Token:
>
> x-jupj3v47dfhf4bpjnyermo2k9jpftdmmfveqgbmppf2kjwgaikfwo5rskbjulisbbwk89ghcqovwruar
> ftlefvanfy5ctes9hehi2mfyoa5grzmk9fldhcft07g52rka
>
> Host: \*.\*.\*.\*:31127

**Response** **Parameters**

> If the returned status code is **200**, the operation is successful.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 30
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> **Table** **5-26** Bodyparameter list

||
||
||
||
||

> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **404**, the requested resource does
> not exist or the URI is incorrect. For details, see the response
> message body.
>
> If the returned status code is **500**, the server is abnormal. For
> details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Content-Type:application/json {
>
> }

**Operation** **Severity**

> Minor

**5.3** **List** **of** **Alarm** **APIs** **for** **FM** **5.3.1**
**Querying** **Alarms**

**Function**

> ThisAPI is used to query alarms on the OSS, including current alarms,
> historical alarms, and alarm logs.

**Precautions**

> 
>
> 
>
> 

You are advised to use exact query with filter criteria (for example,
specifying **AlarmId**) and avoid network-wide query without filter
criteria.

In scenarios where network-wide alarm data is queried, it is recommended
that the query be performed only once a day or during off-peak hours of
the MAE system.

A maximum of five iterative queries can be performed for current alarms.
A maximum of two iterative queries can be performed for historical
alarms and alarm logs.

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 31
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**Call** **Method**

> GET

**URI**

> /api/rest/faultSupervisonManagement/v1/alarms
>
> **Table** **5-27** Header parameter list

||
||
||
||
||

> **Table** **5-28** Queryparameter list

||
||
||
||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 32

MAE-Access

Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||
||
||
||
||

> Remarks:
>
> 1\. If neither **alarmAckState**, **baseObjectInstance**, nor
> **filter** is specified, all alarms are queried by data type by
> default.
>
> **Table** **5-29** Enumeration list of alarmAckState character strings

||
||
||
||
||
||
||
||

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 33

MAE-Access

Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||
||

> **Table** **5-30** Field description of the filter character string

||
||
||
||
||
||

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 34

> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||

**Example** **of** **the** **filter** **Field**

> Filter data based on **csn** and **perceivedSeverity**. The
> relationship between multiple filter criteria is AND.
>
> The JSON character string is as follows:
>
> \[
>
> {
>
> "field": "csn", "operator": "in",
>
> "values": \["19142","19021"\] },
>
> {
>
> "field": "perceivedSeverity", "operator": "in",
>
> "values": \[1,2\] }
>
> \]
>
> Encode the JSON character string using URLEncode and send the encoded
> character string to the filter.
>
> filter=%5B%7B%22field%22%3A%22csn%22%2C%22operator%22%3A%22in%22%2C%
> 22values%22%3A%5B%2219142%22%2C%2219021%22%5D%7D%2C%7B%22field%22
> %3A%22perceivedSeverity%22%2C%22operator%22%3A%22in%22%2C%22values%22%
> 3A%5B1%2C2%2C3%5D%7D%5D

**Sample** **Request**

> HTTP example:
>
> HTTP/1.1 GET
>
> /api/rest/faultSupervisonManagement/v1/alarms?dataType=CURRENT&limit=100
> Host: serverIP:port
>
> Content-Type: application/json Accept: application/json
> Accept-Language: en-US
>
> X-AUTH-TOKEN:
> CA48D152F6B19D84:637C38259E6974E17788348128A430FEE150E874752CE754B6BF855281219925

**Response** **Parameters**

> If the returned status code is **200**, the alarm query is successful.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 35

MAE-Access

Open API Developer Guide (Wireless Network) 5 API List

> **Table** **5-31** Response parameter list

||
||
||
||
||
||
||
||

> **Table** **5-32** Alarm information parameters

||
||
||
||
||
||
||
||
||

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 36

MAE-Access

Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||
||
||
||
||
||
||
||

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 37

> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||
||
||
||
||
||
||
||
||
||

> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **429**, there are too many requests.
> For details, see the response message body.
>
> If the returned status code is **500**, the server is abnormal. For
> details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Date: Mon,24 Dec 2018 10:00:00 GMT
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 38
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> Server: example-server Content-Type: application/json {
>
> "alarmInformationList": \[ {
>
> "alarmId": "4",
>
> "objectInstance": "Server name=OSSSVR01, SvcAgent=irppmengine-3-1,
> SvcName=MAE/MAEAccessIRPPMEngine/mae_access_global, SiteName=Local
> Site",
>
> "notificationType": "notifyNewAlarm", "alarmRaisedTime":
> "1621859460000", "alarmClearedTime": "0",
>
> "alarmType": "10", "probableCause": "", "perceivedSeverity": "2",
>
> "additionalInformation": "IP address=172.28.129.6, Product alias=MAE",
> "ackTime": "0",
>
> "ackUserId": "", "ackState": "0", "clearUserId": "", "cleared": "0",
> "meName": "OSS", "productName": "OSS",
>
> "alarmName": "The OSS Service Is Terminated Abnormally",
> "nativeMoName": "OSS",
>
> "csn": "21559", "subCsn": "0",
>
> "specialAlarmStatus": "0", "comments": ""
>
> } \],
>
> "status": "OperationSucceeded", "marker":
>
> "MjAwJjg2MjI0OTMxNSM5ZDAzYjVkMi0yODQwLTQxZjktYjNjNC0zNjZiZjRiYjJlZjY=",
> "retCode": "90000",
>
> "retMessage": "Query succeeded." }

**Operation** **Severity**

> Minor

**5.4** **List** **of** **Performance** **APIs** **for** **PM**

**5.4.1** **Creating** **a** **Performance** **Data** **Query** **Task**

**Function**

> ThisAPI is used to obtain performance data based on query conditions.
> If the data volume is small, performance data is directly returned
> through this API. If the data volume is large, task information is
> returned and performance data needs to be obtained asynchronously
> according to 5.4.2 Obtaining Performance Data.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 39
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**Precautions**

> 
>
> 
>
> 
>
> 
>
> 

Before creating a query task, ensure that the NE has issued the
measurement subscription of the corresponding counters and the query
period is the same as the period for issuing the subscription.

After the performance result query is complete, you need to immediately
invoke the function described in section 5.4.3 "Deleting a Performance
Result Query Task" to delete the performance result query task to reduce
the system resource usage.

The time range of the query task must be within 24 hours. The number of
counters to be queried cannot exceed 150, and the number of function
subsets to which the counters belong cannot exceed 10.

A maximum of five concurrent requests are supported.

You are advised to specify an NE name to perform an exact query. Do not
use the NE type to perform a network-wide query. If NE types are used
for a network-wide query, it is recommended that the query be performed
only once a day. In addition, do not query data of neighboring cells on
the entire network.

**Call** **Method**

> POST

**URI**

> /api/rest/performanceManagement/v1/measurementResults
>
> **Table** **5-33** Header parameter list

||
||
||
||
||

**Request** **Parameters**

> **Table** **5-34** Bodyparameter list

||
||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 40

MAE-Access

Open API Developer Guide (Wireless Network) 5 API List

> **Table** **5-35** Parameters in the condition MO

||
||
||
||
||
||
||
||
||
||

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 41

> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||
||

**Sample** **Request**

> HTTP example:
>
> POST /api/rest/performanceManagement/v1/measurementResults HTTP/1.1
> Host: \*.\*.\*.\*:31127
>
> Content-Type: application/json Accept: application/json
> Accept-Language: en-US
>
> X-AUTH-TOKEN:
> CA48D152F6B19D84:637C38259E6974E17788348128A430FEE150E874752CE754B6BF855281219925
> {
>
> "timeFormat":"timeString", "startTime": "2021-05-24 00:00:00",
> "endTime": "2021-05-24 00:15:00", "period": 60,
>
> "counterIds":\[ 1526749447, 1526743671
>
> \], "isQueryAllNe": 0,
>
> "neTypeName":"eNodeB", "neNames": \[
>
> "FmaZcc" \]
>
> }
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 42
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**Response** **Parameters**

||
||
||
||
||
||

> If the returned status code is **200**, the request is successful.
>
> If the returned status code is **202**, the request is successful, but
> the query result is not ready. The result needs to be obtained in
> asynchronous mode.
>
> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **404**, the requested resource does
> not exist or the URI is incorrect. For details, see the response
> message body.
>
> If the returned status code is **429**, the request frequency exceeds
> the flow control threshold.
>
> If the returned status code is **500**, the server is abnormal. For
> details, see the response message body.

**Sample** **Response**

> The task is created successfully, and the first batch of data is
> returned. For details about the data structure, see Table 5-38.
>
> HTTP/1.1 200 OK
>
> Mon, 24 May 2021 08:41:26 GMT Server: example-server Content-Type:
> application/json {
>
> "counterIds": \[ 1526749447, 1526743671
>
> \],
>
> "marker": "null", "period": 60, "result": \[
>
> {
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 43
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> "counterValues": \[ "77",
>
> "71" \],
>
> "neFdn": "NE=257", "neName": "FmaZcc",
>
> "objectName":"eNodeB Function Name=31_15, Local Cell ID=3,Cell
> Name=CELL3, eNodeB ID=158435, Cell FDD TDD indication=CELL_TDD",
>
> "startTime": "2021-05-24 00:00:00" },
>
> {
>
> "counterValues": \[ "77",
>
> "85" \],
>
> "neFdn": "NE=257", "neName": "FmaZcc",
>
> "objectName":"eNodeB Function Name=31_15, Local Cell ID=2,Cell
> Name=CELL2, eNodeB ID=158435, Cell FDD TDD indication=CELL_TDD",
>
> "startTime": "2021-05-24 00:00:00" }
>
> \],
>
> "retCode": "90000", "retMessage": "Completed.", "status": 2,
>
> "taskId": "16", "totalSize": 2
>
> }
>
> The task is created successfully, but the data is not returned
> immediately.
>
> HTTP/1.1 202 OK
>
> Content-Type:application/json {
>
> "retCode": "90037",
>
> "retMessage": "The data is being collected.", "taskId": "1569825"
>
> }
>
> The task fails to be created.
>
> HTTP/1.1 400 OK
>
> Content-Type:application/json {
>
> "retCode":"90052",
>
> "retMessage": "The Parameter period value is invalid." }

**Operation** **Severity**

> Minor
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 44
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**5.4.2** **Obtaining** **Performance** **Data**

**Function**

> If a large amount of data is queried, this API needs to be used to
> obtain performance data. If the query task is complete, the
> performance data is returned. Otherwise, polling is required and the
> performance data can be queried only after the task is complete.

**Precautions**

> 

The marker can be left empty except for the first query. Otherwise, the
marker returned by the current task in the last batch of performance
result data needs to be used for each query. If the markers are
inconsistent, the performance result data cannot be obtained.

**Call** **Method**

> GET

**URI**

> /api/rest/performanceManagement/v1/measurementResults/{taskId}
>
> **Table** **5-36** Header parameter list

||
||
||
||
||

**Request** **Parameters**

> **Table** **5-37** Path input parameters

||
||
||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 45
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||

**Sample** **Request**

> First query:
>
> GET
> /api/rest/performanceManagement/v1/measurementResults/23456?limit=5000
> HTTP/1.1
>
> X-Auth-Token:
>
> x-rxvuk4juns6nvy2lg9rz7s44g4oamkmoo5lj0bipo5fzukhc5f9cnz46ljenmr1ijthgdf5hph3v1ghg
> g6pffw49hdob7w8bo54a2l899ho7c5emg6vu9jtdg6050bph
>
> Host: \*.\*.\*.\*:31127
>
> Use the marker to query more batches of result data:
>
> GET
> /api/rest/performanceManagement/v1/measurementResults/234571?limit=5000&marker=8ac
> ea8ca-0dcb-11ea-8000-0050568aff80
>
> HTTP/1.1
>
> X-Auth-Token:
>
> x-rxvuk4juns6nvy2lg9rz7s44g4oamkmoo5lj0bipo5fzukhc5f9cnz46ljenmr1ijthgdf5hph3v1ghg
> g6pffw49hdob7w8bo54a2l899ho7c5emg6vu9jtdg6050bph
>
> Host: \*.\*.\*.\*:31127

**Response** **Parameters**

> **Table** **5-38** Bodyparameter list

||
||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 46

MAE-Access

Open API Developer Guide (Wireless Network) 5 API List

> **Table** **5-39** Bodyparameter list

||
||
||
||
||
||
||
||
||
||
||
||

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 47

> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> **Table** **5-40** Result parameter list

||
||
||
||
||
||
||
||

> If the returned status code is **200**, the request is successful.
>
> If the returned status code is **202**, the request is successful, but
> the query result is not ready. In this case, you need to try again.
>
> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **404**, the requested resource does
> not exist or the URI is incorrect. For details, see the response
> message body.
>
> If the returned status code is **500**, the server is abnormal. For
> details, see the response message body.

**Sample** **Response** **200** HTTP/1.1 200 OK

> Date: Sat, 22 May 2021 09:25:37 GMT Server: example-server
>
> Content-Type: application/json {
>
> "counterIds": \[ 1526728519, 1526728520, 1526728518, 1526728514,
> 1526728515, 1526730594, 1526730595, 1526730592, 1526730593,
> 1526730596, 1526730597,
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 48

MAE-Access

Open API Developer Guide (Wireless Network) 5 API List

> 1526749439, 1526737790
>
> \],
>
> "marker": "aaf85822-badf-11eb-8000-fa163eb450dd", "period": 15,
>
> "result": \[ {
>
> "counterValues": \[ "108",
>
> "69", "313", "338", "145", "983", "402", "657", "818", "472", "762",
> "NIL", "338"
>
> \],
>
> "neFdn": "NE=24327", "neName": "lx_test",
>
> "objectName": "eNodeB Function Name=FM_nsjiahao, Local Cell ID=2, Cell
> Name=FM_nsjiahao_2, eNodeB ID=829, Cell FDD TDD indication=CELL_FDD",
>
> "startTime": "2021-05-19 16:00:00" },
>
> ...... {
>
> "counterValues": \[ "330",
>
> "220", "969", "595", "339", "248", "299", "892", "588", "83", "341",
> "NIL", "598"
>
> \],
>
> "neFdn": "NE=13234", "neName": "LTE_100_005_176",
>
> "objectName": "eNodeB Function Name=FM_nsjiahao, Local Cell ID=0, Cell
> Name=FM_nsjiahao, eNodeB ID=829, Cell FDD TDD indication=CELL_FDD",
>
> "startTime": "2021-05-19 00:00:00" }
>
> \],
>
> "retCode": "90000", "retMessage": "Completed.", "status": 2,

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 49

> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> "taskId": "3", "totalSize": 5000
>
> }

**Sample** **Response** **202** HTTP/1.1 202 OK

> Content-Type:application/json {
>
> "retCode": "90037",
>
> "retMessage": "The data is being collected.", "taskId": "123"
>
> }

**Operation** **Severity**

> Minor

**5.4.3** **Deleting** **a** **Performance** **Result** **Query**
**Task**

**Function**

> ThisAPI is used to delete a task whose performance results have been
> obtained based on the task ID to reduce the system resource usage.

**Precautions**

> 

If this API is not called to delete a task, MAE automatically deletes
the task 12 hours after the task is created. If you want to continue to
obtain data, you need to create a query task again.

**Call** **Method**

> **DELETE**

**URI**

> /api/rest/performanceManagement/v1/measurementResults/{taskId}
>
> **Table** **5-41** Header parameter list

||
||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 50
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||

**Request** **Parameters**

||
||
||
||

**Sample** **Request**

> DELETE
> /api/rest/performanceManagement/v1/measurementResults/0220000052
> HTTP/1.1 X-Auth-Token:
>
> x-rxvuk4juns6nvy2lg9rz7s44g4oamkmoo5lj0bipo5fzukhc5f9cnz46ljenmr1ijthgdf5hph3v1ghg
> g6pffw49hdob7w8bo54a2l899ho7c5emg6vu9jtdg6050bph
>
> Host: \*.\*.\*.\*:31127

**Response** **Parameters**

||
||
||
||
||
||

> If the returned status code is **200**, the request is successful.
>
> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 51
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **404**, the requested resource does
> not exist or the URI is incorrect. For details, see the response
> message body.
>
> If the returned status code is **500**, the server is abnormal. For
> details, see the response message body.

**Sample** **Response**

> The task is deleted successfully.
>
> HTTP/1.1 200 OK
>
> Content-Type:application/json {
>
> "retCode" : "90000", "retMessage" : "Completed.", "taskId" : "3"
>
> }
>
> The task fails to be deleted.
>
> HTTP/1.1 404 OK
>
> Content-Type:application/json {
>
> "retCode" : "90048",
>
> "retMessage" : "Task id does not exist." }

**Operation** **Severity**

> Minor

**5.5** **API** **for** **Querying** **Topology** **Cell**
**Information**

**Function**

> ThisAPI is used to obtain the list of cells in the current topology on
> the OSS.

**Precautions**

> 

In the request message, it is recommended that the number of specified
FDNs be less than or equal to 500. The timeout interval for requesting
the bus is 5 minutes. If there are too many NEs, the request may time
out.

**Call** **Method**

> POST

**URI**

> /api/rest/resourceManagement/v1/topocellsinfo
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 52
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**Request** **Parameters**

> **Table** **5-42** Header parameter list

||
||
||
||
||

> **Table** **5-43** Bodyparameter list

||
||
||
||

> **Table** **5-44** Parameters in theTopocellRequest MO

||
||
||
||

**Sample** **Request**

> POST /api/rest/resourceManagement/v1/topocellsinfo Host: serverIP:port
>
> Content-Type: application/json; charset=UTF-8 X-Auth-Token:
>
> x-jupj3v47dfhf4bpjnyermo2k9jpftdmmfveqgbmppf2kjwgaikfwo5rskbjulisbbwk89ghcqovwruar
> ftlefvanfy5ctes9hehi2mfyoa5grzmk9fldhcft07g52rka
>
> Content-Length:… {
>
> "fdns": \[ "NE=1201"
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 53
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> \] }

**Response** **Parameters**

> If the returned status code is **200**, the operation is successful.
>
> **Table** **5-45** Bodyparameter list

||
||
||
||

> **Table** **5-46** Parameters in the NodeCellInfoSeq MO

||
||
||
||
||
||
||
||

> **Table** **5-47** Parameters in the CellInfo MO

||
||
||
||
||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 54
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||

> **Table** **5-48** Enumeration list of the stateVals character string

||
||
||
||
||
||
||
||

> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **500**, the server is abnormal. For
> details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Content-Type: application/json; charset=UTF-8 Content-Length:…
>
> {
>
> "results": \[ {
>
> "logicBTSDn": "NE=1201", "info": "",
>
> "neDn": "NE=1201", "objectId": 1003224404058, "cellInfos": \[
>
> {
>
> "objDn": "NE=1201,eNodeBCell=0", "cellId": 0,
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 55
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> "stateVals": \[ 0,
>
> 1, \],
>
> "results": \[ "LTE(FDD)", "0", "dualMod", "Unlocked", "Inactive",
> "Enable", "Invalid", ""
>
> \] }, {
>
> "objDn": "NE=1201,eNodeBCell=1", "cellId": 1,
>
> "stateVals": \[ 0,
>
> 2, \],
>
> "results": \[ "LTE(FDD)", "1", "dualMod_1", "Unlocked", "Inactive",
> "Enable", "Invalid", ""
>
> \] }
>
> \] }
>
> \] }

**Operation** **Severity**

> Minor

**5.6** **List** **of** **iSStar** **APIs** **5.6.1** **Creating**
**iSStar** **Task**

**Function**

> ThisAPI is used to create a task based on the iSStar script uploaded
> according to 4.3 (Optional) Deploying iSStar Scripts.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 56
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**Precautions**

> 
>
> 

Currently, the maximum number of concurrent iSStar tasks is 75, and the
maximum number of tasks is 200.

The tasks will be deleted 48 hours after the execution is complete.

**Call** **Method**

> POST

**URI**

> /api/rest/scriptsManagement/v1/tasks

**Request** **Parameters**

> **Table** **5-49** Bodyparameter list

||
||
||
||

> **Table** **5-50** Parameters in the RestCreateJobInputs MO

||
||
||
||
||
||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 57
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||

> **Table** **5-51** Parameters in the scriptParam MO

||
||
||
||

**Sample** **Request**

> HTTP example:
>
> POST /api/rest/scriptsManagement/v1/tasks HTTP/1.1 Host:
> \*.\*.\*.\*:31127
>
> Content-Type: application/json Accept: application/json
> Accept-Language: en-US
>
> X-AUTH-TOKEN:
> CA48D152F6B19D84:637C38259E6974E17788348128A430FEE150E874752CE754B6BF855281219925
> {
>
> "entryScript": "*test.hsp*3", "scriptPath": "*demo*", "startTime":
> "string", "scriptHashValue":
>
> "\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*",
> "scriptParams": \[
>
> {
>
> "data": "test" }
>
> \] }

**Response** **Parameters**

> **Table** **5-52** Bodyparameter list

||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 58

MAE-Access

Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||
||
||

> **Table** **5-53** Parameters in the jobs MO

||
||
||
||
||
||
||
||
||

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 59

> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||
||

> If the returned status code is **200**, the task creation is
> successful.
>
> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid. For details, see the response message
> body.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **404**, the requested resource does
> not exist or the URI is incorrect. For details, see the response
> message body.
>
> If the returned status code is **500**, the request fails to be
> processed. For details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Date: Tue, 7 Jan 2020 10:00:00 GMT Server: example-server
>
> Content-Type: application/json {
>
> "data": \[ {
>
> "jobStatus": "Running",
>
> "retMessage": "Process task successfully.", "id": "15103",
>
> "href":
> "/mnf/10.185.172.143/api/rest/scriptsManagement/v1/tasks/15103",
> "retCode": "0",
>
> "username": "northAPIUser" }
>
> \] }

**Operation** **Severity**

> Minor
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 60
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**5.6.2** **Querying** **iSStar** **Tasks**

**Function**

> ThisAPI is used to obtain the iSStar task execution result based on
> the task ID.

**Precautions**

> 

If the size of the returned result is less than 10 MB, the result is
returned directly. If the size is greater than 10 MB, you need to
download the iSStar task result report by following the instructions
provided in 5.6.4 Downloading the iSStar Task Result Report.

**Call** **Method**

> GET

**URI**

> /api/rest/scriptsManagement/v1/tasks/{jobId}
>
> **Table** **5-54** Queryparameter list

||
||
||
||

**Request** **Parameters** None

**Sample** **Request**

> HTTP example:
>
> GET /api/rest/scriptsManagement/v1/tasks/{jobId} HTTP/1.1 Host:
> \*.\*.\*.\*:31127
>
> Content-Type: application/json Accept: application/json
> Accept-Language: en-US
>
> X-AUTH-TOKEN:
> CA48D152F6B19D84:637C38259E6974E17788348128A430FEE150E874752CE754B6BF855281219925

**Response** **Parameters**

> **Table** **5-55** Bodyparameter list

||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 61

MAE-Access

Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||
||
||

> **Table** **5-56** Parameters in the data MO

||
||
||
||
||
||
||
||
||
||
||
||

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 62

> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||
||
||

> If the returned status code is **200**, the query is successful.
>
> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid. For details, see the response message
> body.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **404**, the requested resource does
> not exist or the URI is incorrect. For details, see the response
> message body.
>
> If the returned status code is **500**, the request fails to be
> processed. For details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Date: Tue, 7 Jan 2020 10:00:00 GMT Server: example-server
>
> Content-Type: application/json {
>
> "data": \[ {
>
> "jobStatus": "Finished", "extCode": "1",
>
> "retMessage": "Process task successfully.", "endTimeGmt":
> "2021-05-20T09:48:56GMT+08:00", "reportUri":
>
> "/mnf/10.185.172.143/api/rest/scriptsManagement/v1/files/15108/result.zip",
> "progress": "100%",
>
> "id": "15108",
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 63
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> "href":
> "/mnf/10.185.172.143/api/rest/scriptsManagement/v1/tasks/15108",
> "retCode": "0",
>
> "jobExecResult": "Failed", "username": "northAPIUser", "extInfo": ""
>
> } \]
>
> }

**Operation** **Severity**

> Minor

**5.6.3** **Deleting** **iSStar** **Tasks**

**Function**

> ThisAPI is used to delete a completed task based on the task ID to
> reduce system resource usage.

**Precautions**

> 

After a task is executed and the task result is downloaded, this API is
called to delete the task to reduce system resource usage. If the task
is not deleted immediately, MAE automatically deletes the task that has
been completed for more than two days.

**Call** **Method**

> DELETE

**URI**

> /api/rest/scriptsManagement/v1/tasks/{jobId}
>
> **Table** **5-57** Queryparameter list

||
||
||
||

**Request** **Parameters** None

**Sample** **Request**

> HTTP example:
>
> DELETE /api/rest/scriptsManagement/v1/tasks/{jobId} HTTP/1.1 Host:
> \*.\*.\*.\*:31127
>
> Content-Type: application/json
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 64
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> Accept: application/json Accept-Language: en-US X-AUTH-TOKEN:
>
> CA48D152F6B19D84:637C38259E6974E17788348128A430FEE150E874752CE754B6BF855281219925

**Delete** **Data**

> Task execution result and task ID in the task list.

**Response** **Parameters**

> **Table** **5-58** Bodyparameter list

||
||
||
||
||
||

> **Table** **5-59** Parameters in the jobs MO

||
||
||
||
||
||
||
||

> If the returned status code is **200**, the deletion is successful.
>
> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 65
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid. For details, see the response message
> body.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **404**, the requested resource does
> not exist or the URI is incorrect. For details, see the response
> message body.
>
> If the returned status code is **500**, the request fails to be
> processed. For details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Date: Tue, 7 Jan 2020 10:00:00 GMT Server: example-server
>
> Content-Type: application/json {
>
> "data": \[ {
>
> "retMessage": "Process task successfully.", "id": "15108",
>
> "href":
> "/mnf/10.185.172.143/api/rest/scriptsManagement/v1/tasks/15108",
> "retCode": "0",
>
> "username": "northAPIUser" }
>
> \] }

**Operation** **Severity**

> Minor

**5.6.4** **Downloading** **the** **iSStar** **Task** **Result**
**Report**

**Function**

> ThisAPI is used to download the result of a task that has been
> executed based on the task ID.

**Precautions**

>  You can download the result report of a task only after the query
> task is complete.

**Call** **Method**

> GET

**URI**

> /mnf/{IP}/api/rest/scriptsManagement/v1/files/{jobId}/result.zip
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 66
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> **Table** **5-60** path parameters

||
||
||
||
||

**Request** **Parameters**

> None

**Sample** **Request**

> HTTP example:
>
> GET /mnf/{IP}/api/rest/scriptsManagement/v1/files/{jobId}/result.zip
> HTTP/1.1 Host: \*.\*.\*.\*:31127
>
> Content-Type: application/json Accept: application/json
> Accept-Language: en-US
>
> X-AUTH-TOKEN:
> CA48D152F6B19D84:637C38259E6974E17788348128A430FEE150E874752CE754B6BF855281219925

**Response** **Parameters**

> If the returned status code is **200**, the download is successful.
>
> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid. For details, see the response message
> body.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **404**, the requested resource does
> not exist or the URI is incorrect. For details, see the response
> message body.
>
> If the returned status code is **500**, the request fails to be
> processed. For details, see the response message body.

**Operation** **Severity**

> Minor
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 67
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**5.7** **List** **of** **System** **Information** **APIs** **5.7.1**
**Testing** **MAE** **Northbound** **Connectivity**

**Function**

> ThisAPI uses the token information returned in 5.1.1 Login API to test
> the MAE northbound connectivity in real time.

**Precautions**

> You have called the API in 5.1.1 Login API to obtain the token
> information.

**Call** **Method**

> POST

**URI**

> /api/rest/oss-info/v1/connection-status

**Request** **Parameters**

> **Table** **5-61** Header parameter list

||
||
||
||

**Sample** **Request**

> POST /api/rest/oss-info/v1/connection-status HTTP/1.1 Host:
> serverIP:port
>
> accessToken: 52661fbd-6b84-4fc2-aa1e-17879a5c6c9b Content-Type:
> application/json; charset=UTF-8 Content-Length:…
>
> { }

**Response** **Parameters**

> If the returned status code is **200**, the API is successfully
> called.
>
> **Table** **5-62** Bodyparameter list

||
||
||

> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 68
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

||
||
||
||

> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **429**, there are too many requests.
> For details, see the response message body.
>
> If the returned status code is **500**, the service is abnormal. For
> details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Content-Type: application/json;charset=UTF-8 Content-Length:…
>
> {
>
> "retCode": 0 }

**Operation** **Severity**

> Minor

**5.7.2** **Querying** **the** **OMC** **Number** **of** **MAE**

**Function**

> ThisAPI uses the token information returned in 5.1.1 Login API to
> query the OMC number of MAE.

**Precautions**

> You have called the API in 5.1.1 Login API to obtain the token
> information.

**Call** **Method**

> GET

**URI**

> /api/rest/oss-info/v1/omcid
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 69
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**Request** **Parameters**

> **Table** **5-63** Header parameter list

||
||
||
||

**Sample** **Request**

> POST /api/rest/oss-info/v1/omcid HTTP/1.1 Host: serverIP:port
>
> accessToken: 52661fbd-6b84-4fc2-aa1e-17879a5c6c9b Content-Type:
> application/json; charset=UTF-8 Content-Length:…
>
> { }

**Response** **Parameters**

> If the returned status code is **200**, the API is successfully
> called.

**Table** **5-64** Bodyparameter list

||
||
||
||

> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **429**, there are too many requests.
> For details, see the response message body.
>
> If the returned status code is **500**, the service is abnormal. For
> details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 70
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List
>
> Content-Type: application/json;charset=UTF-8 Content-Length:…
>
> {
>
> "omcId": "X" }

**Operation** **Severity**

> Minor

**5.7.3** **Querying** **the** **Current** **MAE** **Version**

**Function**

> ThisAPI uses the token information returned in 5.1.1 Login API to
> query the current MAE version.

**Precautions**

> You have called the API in 5.1.1 Login API to obtain the token
> information.

**Call** **Method**

> GET

**URI**

> /api/rest/oss-info/v1/mae-version

**Request** **Parameters**

> **Table** **5-65** Header parameter list

||
||
||
||

**Sample** **Request**

> POST /api/rest/oss-info/v1/mae-version HTTP/1.1 Host: serverIP:port
>
> accessToken: 52661fbd-6b84-4fc2-aa1e-17879a5c6c9b Content-Type:
> application/json; charset=UTF-8 Content-Length:…
>
> { }
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 71
>
> MAE-Access
>
> Open API Developer Guide (Wireless Network) 5 API List

**Response** **Parameters**

> If the returned status code is **200**, the API is successfully
> called.
>
> **Table** **5-66** Bodyparameter list

||
||
||
||

> If the returned status code is **400**, the request is invalid. For
> details, see the response message body.
>
> If the returned status code is **401**, the operation is unauthorized
> and accessSession is invalid.
>
> If the returned status code is **403**, the requester does not have
> the access permission. For details, see the response message body.
>
> If the returned status code is **429**, there are too many requests.
> For details, see the response message body.
>
> If the returned status code is **500**, the service is abnormal. For
> details, see the response message body.

**Sample** **Response**

> HTTP/1.1 200 OK
>
> Content-Type: application/json;charset=UTF-8 Content-Length:…
>
> {
>
> "version": "V100R021C10" }

**Operation** **Severity**

> Minor
>
> Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 72

MAE-Access

Open API Developer Guide (Wireless Network) 6 Error Code List

> **6** **Error** **Code** **List**

||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||
||

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 73

MAE-Access

Open API Developer Guide (Wireless Network) 6 Error Code List

Issue 01 (2021-08-26) Copyright © Huawei Technologies Co., Ltd. 74
