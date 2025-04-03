# openapi_client.DefaultApi

All URIs are relative to *https://api.example.com/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_checkin_links**](DefaultApi.md#get_checkin_links) | **GET** /checkin | Get check-in links


# **get_checkin_links**
> GetCheckinLinks200Response get_checkin_links(pnr)

Get check-in links

### Example


```python
import openapi_client
from openapi_client.models.get_checkin_links200_response import GetCheckinLinks200Response
from openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.example.com/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = openapi_client.Configuration(
    host = "https://api.example.com/v1"
)


# Enter a context with an instance of the API client
with openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = openapi_client.DefaultApi(api_client)
    pnr = 'pnr_example' # str | 

    try:
        # Get check-in links
        api_response = api_instance.get_checkin_links(pnr)
        print("The response of DefaultApi->get_checkin_links:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_checkin_links: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **pnr** | **str**|  | 

### Return type

[**GetCheckinLinks200Response**](GetCheckinLinks200Response.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

