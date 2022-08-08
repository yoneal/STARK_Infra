var STARK_Module_app = {

    api_endpoint: STARK.STARK_Module_url,

    add: function (payload) {
        fetchUrl = this.api_endpoint
        return STARK.request('POST', fetchUrl, payload)
    },

    delete: function (payload) {
        fetchUrl = this.api_endpoint
        return STARK.request('DELETE', fetchUrl, payload)
    },

    update: function (payload) {
        fetchUrl = this.api_endpoint
        return STARK.request('PUT', fetchUrl, payload)
    },

    get: function (data) {
        fetchUrl = this.api_endpoint + '?rt=detail&Module_Name=' + data['Module_Name']
        return STARK.request('GET', fetchUrl)
    },

    list: function (data=[]) {
        fetchUrl = this.api_endpoint + '?rt=all'

        if (data['Next_Token']) {
            next_token = encodeURIComponent(data['Next_Token'])
            fetchUrl = fetchUrl + '&nt=' + next_token;
        }

        return STARK.request('GET', fetchUrl)
    },

    get_field: function (field) {
        fetchUrl = this.api_endpoint + '?rt=get_field&field=' + field
        return STARK.request('GET', fetchUrl)
    },
}

