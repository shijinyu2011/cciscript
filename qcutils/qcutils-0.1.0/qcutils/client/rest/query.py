
import json
import re
import requests

from qcutils.log import Log
from qcutils.exception import QcUtilsDetailedException


class RestQueryException(QcUtilsDetailedException):
    pass


class RestQuery(object):
    requests_mapping = {'post': requests.post, 'get': requests.get, 'put': requests.put, 'delete': requests.delete}

    def __init__(self, path, method, data="", result=200):
        """ Creates a REST query object.

          Keyword arguments:
          path -- Path to the rest object (without the host part). May contain string formatting operators (%) that are later formatted when request function is being called.
          method -- HTTP method used in the request, possible values are 'post', 'get', 'put' and 'delete'
          data -- Payload of the messages. May contain string formatting operators (%) that are later formatted when request function is being called.
          result -- Expected HTTP result code of the response. If some other result code is returned by request call, the RestQueryException is raised.
      """
        self.path = path
        self.method = self.requests_mapping[method]
        self.data = data
        self.result = result

    def request(self, server, headers=None, auth_token=None, url_params=None, params=None, stream=None,
                content_type='application/xml', test_json=False, accept_type='application/json', proxies=None):
        """ Makes the REST query request

            Keyword arguments:
            server -- Path to the server, this cobined with the path given in the constructor and formatted with the url_params is the url that is being used in the request
            headers -- Extra HTTP headers that are needed to fulfill the request
            auth_token -- Possible authorization token, that is being appended as X-Auth-Token HTTP header to the request
            params -- Parameters used to format the query payload using these as formatting parameters for the data given as parameter to the constructor
            stream -- File object, if a contents of a file is used as a request payload instead of the data given as parameter to the constructor
            content_type -- the content type of payload
            test_json -- validates the passed payload so that it's valid JSON
            accept_type -- specifies certain media types which are acceptable for the response

            Return value:
            The default implementation is to return the python data structure containing the response body. Exception is raised, if the
            request fails, e.g. the server doesn't respond or the HTTP result code is something else than the expected one
        """
        if headers is None:
            headers = {}
        if url_params is None:
            url_params = {}
        if params is None:
            params = {}
        if stream:
            data = stream
        else:
            data = self.data % (params)
        path = re.sub(r'%', '%%', self.path)
        return self._send('%s/%s' % (server, path % (url_params)), auth_token, data,
                          headers, content_type, test_json, accept_type, proxies)

    def _send(self, url, auth_token, payload, headers, content_type, test_json, accept_type, proxies):
        if test_json:
            json.loads(payload)
        if content_type:
            headers['Content-Type'] = content_type
        if accept_type:
            headers['Accept'] = accept_type
        if auth_token:
            headers['X-Auth-Token'] = auth_token
        return self._send_request(url, headers, payload, proxies)

    @staticmethod
    def _remove_xml_password(string):
        return re.sub(r'<password>(.*)</password>', '<password>********</password>', string)

    def _send_request(self, url, headers, payload, proxies):
        print_payload = self._remove_xml_password(payload)
        Log.log(5, "payload: %s" % print_payload)
        Log.debug("url: %s" % url)
        Log.log(5, "headers: %s" % headers)
        return self._analyze_result(self.method(url, data=payload, headers=headers, proxies=proxies), headers=headers)

    def _analyze_result(self, response, headers=None):
        """ This function could be overriden if the response might contain more than one acceptable return codes """
        Log.debug("result: %d" % response.status_code)
        Log.log(5, "response text: %s" % response.text)
        Log.log(5, "response headers: %s" % response.headers)
        if headers:
            Log.log(5, "headers: %s" % headers)

        if response.status_code == self.result:
            return self._parse_result_parameters(response)

        raise RestQueryException("Status code mismatch, expected %d, got %d" %
                                 (self.result, response.status_code), response.text)

    def _parse_result_parameters(self, response):
        """ This function should be overriden by the subclass, the default action is to expect the output
            to be JSON and convert it to python data structure (and return that) """
        return json.loads(response.text)


class RestHeaderQuery(RestQuery):

    def _parse_result_parameters(self, response):
        """ This function should be overriden by the subclass, the default action is to expect the output
            to be JSON and convert it to python data structure (and return that) """
        return response.headers


if __name__ == "__main__":
    pass
