---
created: 2026-05-14T16:56:12 (UTC -05:00)
tags: []
source: https://help.keepcon.app/?epkb_post_type_1=keepcon-cem-search-api
author: 
---

# Keepcon CEM Search API – Keepcon

> ## Excerpt
> Última actualización23/01/2024

---
Última actualización23/01/2024

## Keepcon Integrations

1.  **Main Objects**

**Content**

Content object represents a piece of content published in a social network like Twitter, Facebook, Instagram, etc. Content has the text, information about the author and other attributes like date created, sentiment and classification.

Each Content is automatically processed by Keepcon classification engine. Keepcon Classification enhances each Content with the following dimensions:

-   Tags using the Taxonomy built for each Account
-   Sentiment Analysis
-   Information Extraction configured for each Account. For example: Phone number, Social Security Number, Address, Invoice ID, Client ID, etc.
-   Cloud of words
-   User Profile augmentation

**User Profile**

User Profile object represents a user that interact with a company in social networks. One User Profile may interact though different social networks. For example, if one person writes messages in Facebook and Twitter, he will have two social users, but both social users will be merged into one User Profile. 

Logic for merging social users into User Profiles is defined for each account. The company may request Keepcon to merge social users using extracted information about phone number, social security id, client id or any other attribute of its business.  

User Profile also has a list of Intelligent Tags that may represent a set of interests for that person, mood, hobbies, etc. 

2.  **Authorization and Security** 

For every request you should add a parameter access\_token={ACCESS-TOKEN}. You can access and renew your token at the configuration section of the application.

You must use HTTPS for every request.

You should try to use the latest version of the API.

3.  [**Rate Limits**](https://developer.zendesk.com/rest_api/docs/core/introduction#rate-limits)

We only allow a certain number of requests per minute depending on your plan and the endpoint. We reserve the right to adjust the rate limit for given endpoints to provide a high quality of service for all clients. 

4.  **Retrieving information from Keepcon**

Objects that reside into Keepcon’s platform could be accessed using CEM API endpoints. Through this API you can export and modify the following objects:

-   Contents along with its automatic and manual classification. We allow several ways of requesting a set of contents using different kinds of parameters like a range of dates, specific automatic classifier, etc. 
-   User profiles: This includes the social information of each user (merging Facebook and Twitter identities). 

2.  Content API

By using this API you can get the classification of Content inside Keepcon system.

|POST|**accounts/{account-number}/content/search**|Search contents by query|
|---|---|---|
|GET|**accounts/{account-number}/content/ {id}**|Get a content requesting by id|
|GET|**accounts/{account-number}/groups**|Get groups defined in the account|
|GET|**accounts/{account-number}/tag\_hierarchy**|Get tag hierarchy defined in the account|

1.  **Search Contents by Query**

You can access a set of Content objects by specifying a search query

POST https://api.keepcon.com/ accounts/{account-number}/content/search?access\_token=ACCESS\_TOKEN

Body of that request should specify the desired search query. Search query can include the following parameters:

|**Parameter**|**Description**|**Type**|
|---|---|---|
|created\_at\_from|Filter content created after this datetime|datetime|
|created\_at\_to|Filter content created before this datetime|datetime|
|updated\_at\_from|Filter content updated after this datetime|datetime|
|updated\_at\_to|Filter content updated before this datetime|datetime|
|groups|Filter by group. Groups are defined in the account.|Array|
|sources|Filter content by source. Available sources: 
– whatsapp
– facebook
– twitter
– instagram
– youtube
– email
– webchat
– google\_play
– apple\_app\_store
– linkedin
– google\_search
– google-my-business|Array|
|content\_types|Filter content by type. Available content\_types:
– Facebook: fb-comment, fb-message, fb-post
– Twitter: retweet, tweet, direct-message, quote
– Instagram: ig-message, ig-media,  ig-comment, ig-image, ig-story, ig-videoinstagram\_business\_discovery\_listening\_media, instagram\_listening\_media 
– Youtube: yt-comment, yt-video
– Appstore: apple\_app\_store\_review\_comment
– Google Play: gp\_review\_comment
– Google My Business: google-my-business-review, google-my-business-reply
– LinkedIn: li-comment, li-post
– Webchat: webchat-message, webchat-start
– Whatsapp: whatsapp\_message
– Email: email
– Google Search: google\_search\_result|Array|

For example:

![](https://help.keepcon.app/wp-content/uploads/2023/08/image-2.png)

Response for this request is a list of content that match with the search criteria and will have the following format:

You should use next\_page\_token to iterate results until next\_page\_token is null. For example:

POST https://api.keepcon.com/ accounts/{account-number}/content/search?access\_token=ACCESS\_TOKEN&next\_page\_token=NEXT\_PAGE\_TOKEN

2.  **Get Content by ID**

You can access details about a specific content requesting it by the Keepcon Social Content ID (the “id” field given in the Search Contents By Query response). This API retrieves a specific Content.

GET https://api.keepcon.com/accounts/{account-number}/content/{id}

Response to that request:

![](https://help.keepcon.app/wp-content/uploads/2023/08/image-3.png)

3.  User Profiles API

1.  **General considerations**

-   Access token is provided by Keepcon support team.
-   Account-number is provided by Keepcon support team.
-   List of user attributes should be configured on each account.

2.  **GET accounts/****{account-number}****/profiles/list**

https://api.keepcon.com/ accounts/{account-number}/profiles/list

1.  **Response**

2.  **Description**

-   Response is a collection of users. Each user with one or several profiles. Each user corresponds to a particular social network, indicated by the field _type_. It follows on below the available _type_ options:
    -   whatsapp
    -   facebook
    -   twitter
    -   instagram
    -   youtube
    -   email
    -   webchat
    -   google\_play
    -   apple\_app\_store
    -   linkedin
    -   google\_search
    -   google-my-business

-   The collection is always sorted by updated\_at field in descending order.
-   next\_page should be used as parameter to iterate. If next\_page is not present there are no more results to iterate. 
-   Attributes may be automatically extracted by keepcon robot or by entered by a human operator.
-   Created\_at is the epoch format in milliseconds of the first interaction of the user.
-   Updated\_at is the epoch format in milliseconds of the last update for any attribute of the profile. Not the last interaction of the user.

3.  **Parameters**

-   ACCESS\_TOKEN: A valid access token
-   NEXT\_PAGE: Id of the next page

3.  **GET accounts/****{account-number}****/profiles/****{profile-id}**

https://api.keepcon.com/ accounts/{account-number}/profiles/{profile-id}

1.  **Response**

2.  **Description**

-   Get information for a profile. User may have one or several profiles. Each user corresponds to a particular social network, indicated by the field _type_. It follows on below the available _type_ options:
    -   whatsapp
    -   facebook
    -   twitter
    -   instagram
    -   youtube
    -   email
    -   webchat
    -   google\_play
    -   apple\_app\_store
    -   linkedin
    -   google\_search
    -   google-my-business
-   Value of {profile-id} is the unique ID of keepcon system.
-   Attributes may be automatically extracted by keepcon robot or by entered by a human operator.
-   Created\_at is the epoch format in milliseconds of the first interaction of the user.
-   Updated\_at is the epoch format in milliseconds of the last update for any attribute of the profile. Not the last interaction of the user.

3.  **Parameters**

-   ACCESS\_TOKEN: A valid access token

4.  **GET accounts/****{account-number}****/profiles****/****{social-network}/{social-user-id}**

https://api.keepcon.com/ accounts/{account-number}/profiles/{social-network}/{social-id}

1.  **Response**

2.  **Description**

-   Get information for a profile linked to a specific user. User may have one or several profiles. Each user corresponds to a particular social network, indicated by the field _type_.  It follows on below the available _type_ options:
    -   whatsapp
    -   facebook
    -   twitter
    -   instagram
    -   youtube
    -   email
    -   webchat
    -   google\_play
    -   apple\_app\_store
    -   linkedin
    -   google\_search
    -   google-my-business
-   Value of {social-network } should be ‘twitter’, ‘facebook’, ‘instagram’, ‘youtube’, ‘email’.
-   Value of {social-user-id} is the unique identifier on each social network.
-   Attributes may be automatically extracted by keepcon robot or by entered by a human operator.
-   Created\_at is the epoch format in milliseconds of the first interaction of the user.
-   Updated\_at is the epoch format in milliseconds of the last update for any attribute of the profile. Not the last interaction of the user.

3.  **Parameters**

-   ACCESS\_TOKEN: A valid access token

¿Te gustó este artículo?
