---
created: 2026-05-14T16:54:43 (UTC -05:00)
tags: []
source: https://help.keepcon.app/?epkb_post_type_1=keepcon-profiles-api
author: 
---

# Keepcon Profiles API – Keepcon

> ## Excerpt
> Última actualización07/05/2024

---
Última actualización07/05/2024

## **1\. User Profiles Endpoints**

|GET|**accounts/{account-number}/profiles/list**|**Get a list of profiles within an account.**|
|---|---|---|
|GET|**accounts/{account-number}/profiles/{profile-id}**|Get information about one profile.|
|GET|**accounts/{account-number}/profiles/{social-network}/{social-user-id}**|Get profiles by social network and username|
|POST|**accounts/:account\_id/profiles/{social-network}/{social-user-id}**|Update a profile attribute based on social network parameters|
|POST|**accounts/:account\_id/profiles/:profile\_id**|Update a profile attribute based on a profile id|
|POST|**private/profiles**|Creates an user profile if not exists|
|POST|**private/accounts/:account\_id/profiles/:content\_id**|Update a profile attribute based on keepcon content id|

### 1.1 General considerations

-   Access token is provided by Keepcon support team.
-   Account-number is provided by Keepcon support team.
-   List of user attributes should be configured on each account.
-   Automatic information extraction depends on each account configuration.

### 1.2 **GET accounts/{account-number}/profiles/list**

`https://api.keepcon.com/accounts/{account-number}/profiles/list?access_token=ACCESS-TOKEN`

`https://api.keepcon.com/accounts/{account-number}/profiles/list?access_token=ACCESS-TOKEN&page_token=PAGE_TOKEN`

`https://api.keepcon.com/ accounts/{account-number}/profiles/list?access_token=ACCESS-TOKEN&required_attributes_any=field_1,field_2&required_attributes_all=field_3,ield_4&tags=tag12`

#### 1.2.1 Response

`{  "results": [{  " id": "dskadj3834243n",  "social_users": [{  "type": "twitter",  "social_network_id": “123456”,  "name": "Damian Sabelli",  "username": "@Damian_Sabelli",  "location": "CABA, Argentina",  "followers": 20,  "link": "http://www.twitter.com/Damian_Sabelli",          "gender": "male",  "description": "me gusta la musica"  },  {  "type": "facebook",  "social_network_id": “11111”,  "name": "Damian Sabelli",  "gender": "male",  "username": "Damian Sabelli",  "link": "https://www.facebook.com/app_scoped_user_id/11111/"  }],  "attributes": {  "phone": [{ "value": "5413-5582","source": "operator"}],  "geolocation": [{"value": "-34.556985,-58.449555","source": "operator"}],  "gender": [{"value": "male","source": "operator"}],  "direccion": [{"value": "25 de Mayo 2112","source": "operator"}],  "dni": [{ "value": "23.555.666","source": "operator"}],  "mail": [{ "value": "damian@gmail.com","source": "operator"}]  },  "created_at": 23424234324,,    "updated_at": 2734832743  },  …],  “page_token”: “asd324234jssrewr3sdfgsgfsgrs”  }`

#### 1.2.2 Description

-   Response is a collection of profiles. Each profile with one or several social users. Each social users corresponds to a particular social network such as:
    -    apple\_app\_store
    -    clipping
    -   email
    -   facebook
    -   google-my-business
    -   google\_play
    -   instagram
    -   instagramComment
    -   instagramMedia
    -   linkedin
    -   tiktok
    -   twitter
    -   webchat
    -   whatsapp
    -   youtube
-   The collection is always sorted by updated\_at field in descending order.
-   next\_page should be used as parameter to iterate. If next\_page is not present there are no more results to iterate. 
-   Attributes may be automatically extracted by keepcon robot or by entered by a human through this Api or keepcon’s platform (operator).
-   Created\_at is the epoch format in milliseconds of the first interaction of the user.
-   Updated\_at is the epoch format in milliseconds of the last update for any attribute of the profile or an update on profile social users. Not the last interaction of the user.
-   Page token expires after 3 (three) minutes.

-   In case unexisting profile attributes are used in required\_attributes\_all or required\_attributes\_any, the following error message will appear as a response:

`{  "**error**"**:** "invalid attribute(s): telefon. valid attributes are: telefono, n_mero_de_tr_mite, nombre, email, dni, direcci_n, apellido"  }`

#### 1.2.3 **Parameters**

-   ACCESS\_TOKEN: A valid access token
-   NEXT\_PAGE: Id of the next page

-   ACCESS\_TOKEN: A valid access token
-   NEXT\_PAGE: Id of the next page
-   required\_attributes\_any (optional): List of profile attributes codes separated by commas where at least one attribute must have been completed for the profile(s) to be brought.

|**`https://api.keepcon.com/accounts/{account-number}/profiles/list?access_token=ACCESS-TOKEN&required_attributes_any=telefono,email`**|
|---|
|`{  "results": [  {  "id": "d55cbc1a-0b64-11ef-a62f-35a7960b157e",  "social_users": [  {  "type": "twitter",  "social_network_id": "1098297653438439424",  "name": "Cutie",  "username": "Cutiemutieq",  "location": "Acapulco De Juarez, Guerrero, Mexico",  "gender": "unknown",  "link": "http://www.twitter.com/Cutiemutieq",  "description": "Bilkent Üniversitesi`, `Dogs !, Music, Art, Motorbikes, Movies, Tennis, Yogi, Dogs again, Awareness of awareness, Jai Guru Dev.",  "followers": "664"  }  ],  "attributes": {  "passport": [  {  "value": "CR22334455",  "source": "operator"  }  ]  },  "description": "",`
`"tags": [],  "created_at": 1714971317603,  "updated_at": 1715091434526  },  {  "id": "02e08ec2-0bd9-11ef-8af9-4b164d5ae8cb",  "social_users": [  {  "type": "twitter",  "social_network_id": "1733118473524445184",  "name": "Sa",  "username": "iies0x",  "location": "Arab, Alabama, United States",  "gender": "female",  "link": "http://www.twitter.com/iies0x",  "followers": "131"`
`}  ],  "attributes": {  "edad": [  {  "value": 30,  "source": "operator"  }  ]  },  "description": "",  "tags": [],  "created_at": 1715021215585,  "updated_at": 1715091420278  }  ],  "count": 2,  "total_count": 2  }`|

-   required\_attributes\_all (optional):List of profile attributes codes separated by commas where all attributes must have been completed for the profile(s) to be brought.

|**`https://api.keepcon.com/accounts/{account-number}/profiles/list?access_token=ACCESS-TOKEN&required_attributes_all=passport,edad`**|
|---|
|`{  "results": [  {  "id": "57b35056-09a4-11ef-9f4f-05ce0059e980",  "social_users": [  {  "type": "twitter",  "social_network_id": "1499702102507274245",  "name": "Bravo by Kate",  "username": "BravobyKate",  "location": "Australia, Coahuila De Zaragoza, Mexico",  "gender": "male",  "link": "http://www.twitter.com/BravobyKate",  "description": "Merce is in the purse.",  "followers": "1097"  }  ],  "attributes": {  "edad": [  {  "value": 20,  "source": "operator"  }  ],  "passport": [  {  "value": "FR23123212",  "source": "operator"  }  ]  },  "description": "",  "tags": [],  "created_at": 1714778692242,  "updated_at": 1715091676617  }  ],  "count": 1,  "total_count": 1  }`|

-   tags (optional)s: List of profile tags separated by commas where at least one tag must have been completed for the profile(s) to be brought.

|**`https://api.keepcon.com/accounts/{account-number}/profiles/list?access_token=ACCESS-TOKEN&tags=Otros,Cliente Latam`**|
|---|
|`{  "results": [  {  "id": "4a037404-0990-11ef-9d63-31fdd7d391db",  "social_users": [  {  "type": "twitter",  "social_network_id": "1250621600442880000",  "name": "Goodtea",  "username": "goodTea56",  "location": "Unrecognized",  "gender": "female",  "link": "http://www.twitter.com/goodTea56",  "description": "❗WARNING❗\n\nakun ini isinya sampah doang\nyang mau unfollow silahkan ~manusia yang sedang menghabiskan jatah gagal",  "followers": "42"  }  ],  "attributes": {},  "description": "",  "tags": [  "No Cliente\t",  "Otros"  ],  "created_at": 1714770079345,  "updated_at": 1715092012218  },  {  "id": "4a03d2fa-0990-11ef-a0cc-7b3d659fb19a",  "social_users": [  {  "type": "twitter",  "social_network_id": "1480133083818971138",  "name": "kia.",  "username": "jyozy0",  "location": "Unrecognized",  "gender": "female",  "link": "http://www.twitter.com/jyozy0",  "description": "real, at least tries to be.",  "followers": "1774"`
`}  ],  "attributes": {},  "description": "",  "tags": [  "Cliente Latam"  ],  "created_at": 1714770079347,  "updated_at": 1715091865914  }  ],  "count": 2,  "total_count": 2  }`|

### 1.3 **GET accounts/{account-number}/profiles/{profile-id}**

`https://api.keepcon.com/accounts/{account-number}/profiles/{profile-id}?access_token=ACCESS-TOKEN`

#### 1.3.1 Response

`{  " id": "dskadj3834243n",  "social_users": [{  "type": "twitter",  "social_network_id": “123456”,  "name": "Damian Sabelli",  "username": "@Damian_Sabelli",  "location": "CABA, Argentina",  "followers": 20,  "link": "http://www.twitter.com/Damian_Sabelli",          "gender": "male",  "description": "me gusta la musica"  },  {  "type": "facebook",  "social_network_id": “11111”,  "name": "Damian Sabelli",  "gender": "male",  "username": "Damian Sabelli",  "link": "https://www.facebook.com/app_scoped_user_id/11111/"  }],  "attributes": {  "phone": [{ "value": "5413-5582","source": "operator"}],  "geolocation": [{"value": "-34.556985,-58.449555","source": "operator"}],  "gender": [{"value": "male","source": "operator"}],  "direccion": [{"value": "25 de Mayo 2112","source": "operator"}],  "dni": [{ "value": "23.555.666","source": "operator"}],  "mail": [{ "value": "damian@gmail.com","source": "operator"}]  },  "created_at": 23424234324,,    "updated_at": 2734832743  }`

#### 1.3.2 Description

-   Get information for a user. User may have one or several profiles. Each profile corresponds to a particular social network (facebook, twitter, etc.).
-   Value of {profile-id} is the unique ID of keepcon system.
-   Attributes may be automatically extracted by keepcon robot or by entered by a human through this Api or keepcon’s platform (operator).
-   Created\_at is the epoch format in milliseconds of the first interaction of the user.
-   Updated\_at is the epoch format in milliseconds of the last update for any attribute of the profile or an update on profile social users. Not the last interaction of the user.

#### 1.3.3 Parameters

-   ACCESS\_TOKEN: A valid access token

### 1.4 **GET accounts/{account-number}/profiles/{social-network}/{social-user-id}**

`https://api.keepcon.com/accounts/{account-number}/profiles/{social-network}/{social-id}?access_token=ACCESS-TOKEN`

#### 1.4.1 Response

`{  " id": "dskadj3834243n",  "social_users": [{  "type": "twitter",  "social_network_id": “123456”,  "name": "Damian Sabelli",  "username": "@Damian_Sabelli",  "location": "CABA, Argentina",  "followers": 20,  "link": "http://www.twitter.com/Damian_Sabelli",          "gender": "male",  "description": "me gusta la musica"  },  {  "type": "facebook",  "social_network_id": “11111”,  "name": "Damian Sabelli",  "gender": "male",  "username": "Damian Sabelli",  "link": "https://www.facebook.com/app_scoped_user_id/11111/"  }],  "attributes": {  "phone": [{ "value": "5413-5582","source": "operator"}],  "geolocation": [{"value": "-34.556985,-58.449555","source": "operator"}],  "gender": [{"value": "male","source": "operator"}],  "direccion": [{"value": "25 de Mayo 2112","source": "operator"}],  "dni": [{ "value": "23.555.666","source": "operator"}],  "mail": [{ "value": "damian@gmail.com","source": "operator"}]  },  "created_at": 23424234324,,    "updated_at": 2734832743  }`

#### 1.4.2 Description

-   Get information for a user. User may have one or several profiles. Each profile corresponds to a particular social network (facebook, twitter, etc.). 
-   Value of {social-network } should be ‘twitter’, ‘facebook’, etc.
-   Value of {social-user-id} is the unique identifier on each social network.
-   Attributes may be automatically extracted by keepcon robot or by entered by a human through this Api or keepcon’s platform (operator).
-   Created\_at is the epoch format in milliseconds of the first interaction of the user.
-   Updated\_at is the epoch format in milliseconds of the last update for any attribute of the profile or an update on profile social users. Not the last interaction of the user.

#### 1.4.3 Parameters

-   ACCESS\_TOKEN: A valid access token

### 1.5 **POST accounts/:account\_id/profiles/{social-network}/{social-user-id}**

`https://api.keepcon.com/accounts/:account_id/profiles/{social-network}/{social-user-id}?access_token=ACCESS-TOKEN`

#### 1.5.1 body

`{   "update":   {  "phone": 5491112356478,  “twitter_account”: “keepcon”  }  }`

#### 1.5.2 Response

**– If profile attribute is defined:**

`{    "success": true  }`

**– If profile attribute is not defined:**

`{    "success": false,    "error": "attribute 'address' is not defined in account settings"  }`

#### 1.5.3 Description

-   Create/Update a collection of profile attributes.  
-   Value of {social-network } should be ‘twitter’, ‘facebook’, etc.
-   Value of {social-user-id} is the unique identifier on each social network.

#### 1.5.4 **Parameters**

-   ACCESS\_TOKEN: A valid access token

### 1.6 **POST accounts/:account\_id/profiles/:profile\_id**

`https://api.keepcon.com/accounts/:account_id/profiles/:profile_id?access_token=ACCESS-TOKEN`

#### 1.6.1 body

`{   "update":   {  "phone": 5491112356478,  “twitter_account”: “keepcon”  }  }`

#### 1.6.2 Response

**– If profile attribute is defined:**

`{    "success": true  }`

**– If profile attribute is not defined:**

`{    "success": false,    "error": "attribute 'telesfadafono' is not configured in account settings"  }`

#### 1.6.3 Description

-   Create/Update a collection of profile attributes. 
-   Value of {profile\_id} is keepcon unique profile id.

#### 1.6.4 Parameters

-   ACCESS\_TOKEN: A valid access token

### 1.7 **POST private/profiles**

`https://api.keepcon.com/private/profiles?access_token=ACCESS-TOKEN`

#### 1.7.1 body

`{   "content_id": “10153611381166243_10153983242926243-KeepconFBCommentTest-inbox-39”  }`

#### 1.7.2 Response

`{    "success": true  }`

#### 1.7.3 Description

-   Creates an user profile and a social user from a social content if they are not created yet. 

#### 1.7.4 Parameters

-   ACCESS\_TOKEN: A valid access token

### 1.8 **POST private/accounts/:account\_id/profiles/:content\_id**

`https://api.keepcon.com/private/accounts/:account_id/profiles/:content_id?access_token=ACCESS-TOKEN`

#### 1.8.1 body

`{   "update":   {  "phone": 5491112356478,  “twitter_account”: “keepcon”  }  }`

#### 1.8.2 Response

**– If profile attribute is defined:**

`{    "success": true  }`

**– If profile attribute is not defined:**

`{    "success": false,    "error": "attribute 'telesfadafono' is not configured in account settings"  }`

#### 1.8.3 Description

-   Create/Update a collection of profile attributes.  
-   Value of {content\_id} is keepcon social content id.

#### 1.8.4 Parameters

-   ACCESS\_TOKEN: A valid access token

Observaciones Internas:

Los atributos del profile tienen un único source y valor, si se sobreescribe se pierde el anterior. Se podrian guardar todos (a definir).

### 2 **Internal general considerations**

### 2.1 **token**

Token provided by keepcon are crm’s users tokens. A token is allowed to operate on a profile if that user has access to that account. Tokens related to keepcon’s users are allowed to operate on every account regardless of the user-account relation.

If access token is invalid or user doens’t has access to the account a http 401 status is returned with an error explaining this.

### 2.2 **Private endpoints**

Private endpoints are used for internal keepcon use. They were thought to be used from storm topology (create profile bolt and information extraction bolt) at first.

### 2.3 **Information extraction configuration**

Information extraction is defined in account setting configuration. The configuration must look like:

  `"profiles": {      "extraction_fields": {        "dni": "id cliente",        “extraction_field”: “profile_attribute”      }  }`

where:

– _extraction\_field_ is the name of the field given by the extraction service

– _profile\_attribute_: is the name of the profile attribute where the extraction\_field is mapped. Note that if profile\_attribute doesn’t exist, the information extraction bolt is going to fail because it checks that the attribute is defined.

### 2.4 **Attributes are not multivalued**

Each attribute can store only one value at a time. If an attribute is updated by a human or by the information extraction bolt the old value is deleted.

Ante cualquier duda consultar al responsable asignado a su cuenta.

___

¿Te gustó este artículo?
