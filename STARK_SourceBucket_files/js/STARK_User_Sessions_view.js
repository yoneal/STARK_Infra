var root = new Vue({
    el: "#vue-root",
    data: {
        metadata: {
            'Session_ID': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': ''
            },
            'Username':  {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': ''
            },
            'Sess_Start':  {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': ''
            },
            'TTL':  {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': ''
            },
            'Permissions':  {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': ''
            },
        },            
        auth_config: { },
        auth_list: {
            'View': {'permission': 'User Sessions|View', 'allowed': false},
            'Add': {'permission': 'User Sessions|Add', 'allowed': false},
            'Delete': {'permission': 'User Sessions|Delete', 'allowed': false},
            'Edit': {'permission': 'User Sessions|Edit', 'allowed': false},
            'Report': {'permission': 'User Sessions|Report', 'allowed': false}
        },
        listview_table: '',
        STARK_report_fields: [],
        STARK_User_Sessions: {
            'Session_ID': '',
            'sk': '',
            'Username': '',
            'Sess_Start': '',
            'TTL': '',
            'Permissions': '',
        },
        custom_report:{
            'Session_ID': {"operator": "", "value": "", "type":"S"},
            'Username':  {"operator": "", "value": "", "type":"S"},
            'Sess_Start':  {"operator": "", "value": "", "type":"S"},
            'TTL':  {"operator": "", "value": "", "type":"S"},
            'Permissions':  {"operator": "", "value": "", "type":"S"},
            'STARK_isReport':true,
            'STARK_report_fields':[]
        },
        lists: {
            'Report_Operator': [
                { value: '', text: '' },
                { value: '=', text: 'EQUAL TO (=)' },
                { value: '<>', text: 'NOT EQUAL TO (!=)' },
                { value: '<', text: 'LESS THAN (<)' },
                { value: '<=', text: 'LESS THAN OR EQUAL TO (<=)' },
                { value: '>', text: 'GREATER THAN (>)' },
                { value: '>=', text: 'GREATER THAN OR EQUAL TO (>=)' },
                { value: 'contains', text: 'CONTAINS (%..%)' },
                { value: 'begins_with', text: 'BEGINS WITH (..%)' },
                { value: 'IN', text: 'IN (value1, value2, value3, ... valueN)' },
                { value: 'between', text: 'BETWEEN (value1, value2)' },
            ],
        },
        list_status: {
        },
        multi_select_values: {

        },
        visibility: 'hidden',
        next_token: '',
        next_disabled: true,
        prev_token: '',
        prev_disabled: true,
        page_token_map: {1: ''},
        curr_page: 1,
        showReport: false,
        object_url_prefix: "",
        temp_csv_link: "",
        temp_pdf_link: "",
        showError: false,
        no_operator: [],
        error_message: '',
        authFailure: false,
        authTry: false,

    },
    methods: {

        show: function () {
            this.visibility = 'visible';
        },

        hide: function () {
            this.visibility = 'hidden';
        },

        add: function () {
            loading_modal.show()
            console.log("VIEW: Inserting!")

            let data = { STARK_User_Sessions: this.STARK_User_Sessions }

            STARK_User_Sessions_app.add(data).then( function(data) {
                console.log("VIEW: INSERTING DONE!");
                loading_modal.hide()
                window.location.href = "STARK_User_Sessions.html";
            }).catch(function(error) {
                console.log("Encountered an error! [" + error + "]")
                alert("Request Failed: System error or you may not have enough privileges")
                loading_modal.hide()
            });
        },

        delete: function () {
            loading_modal.show()
            console.log("VIEW: Deleting!")

            let data = { STARK_User_Sessions: this.STARK_User_Sessions }

            STARK_User_Sessions_app.delete(data).then( function(data) {
                console.log("VIEW: DELETE DONE!");
                console.log(data);
                loading_modal.hide()
                window.location.href = "STARK_User_Sessions.html";
            })
            .catch(function(error) {
                console.log("Encountered an error! [" + error + "]")
                alert("Request Failed: System error or you may not have enough privileges")
                loading_modal.hide()
            });
        },

        update: function () {
            loading_modal.show()
            console.log("VIEW: Updating!")

            let data = { STARK_User_Sessions: this.STARK_User_Sessions }

            STARK_User_Sessions_app.update(data).then( function(data) {
                console.log("VIEW: UPDATING DONE!");
                console.log(data);
                loading_modal.hide()
                window.location.href = "STARK_User_Sessions.html";
            })
            .catch(function(error) {
                console.log("Encountered an error! [" + error + "]")
                alert("Request Failed: System error or you may not have enough privileges")
                loading_modal.hide()
            });
        },

        get: function () {
            const queryString = window.location.search;
            const urlParams = new URLSearchParams(queryString);
            //Get whatever params are needed here (pk, sk, filters...)
            data = {}
            data['Session_ID'] = urlParams.get('Session_ID');

            if(data['Session_ID'] == null) {
                root.show();
            }
            else {
                loading_modal.show();
                console.log("VIEW: Getting!")

                STARK_User_Sessions_app.get(data).then( function(data) {
                    root.STARK_User_Sessions = data[0]; //We need 0, because API backed func always returns a list for now
                    root.STARK_User_Sessions.orig_Session_ID = root.STARK_User_Sessions.Session_ID;
                    console.log("VIEW: Retreived module data.")
                    root.show()
                    loading_modal.hide()
                })
                .catch(function(error) {
                    console.log("Encountered an error! [" + error + "]")
                    alert("Request Failed: System error or you may not have enough privileges")
                    loading_modal.hide()
                });
            }
        },

       list: function (lv_token='', btn='') {
            spinner.show()
            data = {}
            data['stark_permissions'] = this.stark_permissions
            STARK.auth(data).then( function(data) {
                console.log("Auth Request Done!");
                console.log(data);
                root.stark_permissions = data;
            })
            .catch(function(error) {
                console.log("Encountered an error! [" + error + "]")
                alert("Request Failed: System error or you may not have enough privileges")
                loading_modal.hide()
            });
            payload = []
            if (btn == 'next') {
                root.curr_page++;
                console.log(root.curr_page);
                payload['Next_Token'] = lv_token;

                //When Next button is clicked, we should:
                // - save Next Token to new page in page_token_map
                // - hide Next button - it will be visible again if API call returns a new Next Token
                // - if new_page is > 2, assign {new_page - 1} token to prev_token
                root.prev_disabled = false;    
                root.next_disabled = true;

                root.page_token_map[root.curr_page] = lv_token;

                if (root.curr_page > 1) {
                    root.prev_token = root.page_token_map[root.curr_page - 1];
                }
                console.log(root.page_token_map)
                console.log(root.prev_token)
            }
            else if (btn == "prev") {
                root.curr_page--;

                if (root.prev_token != "") {
                    payload['Next_Token'] = root.page_token_map[root.curr_page];
                }

                if (root.curr_page > 1) {
                    root.prev_disabled = false
                    root.prev_token = root.page_token_map[root.curr_page - 1]
                }
                else {
                    root.prev_disabled = true
                    root.prev_token = ""
                }
            }

            STARK_User_Sessions_app.list(payload).then( function(data) {
                token = data['Next_Token'];
                root.listview_table = data['Items'];
                console.log("DONE! Retrieved list.");
                spinner.hide()

                if (token != "null") {
                    root.next_disabled = false;
                    root.next_token = token;
                }
                else {
                    root.next_disabled = true;
                }

            })
            .catch(function(error) {
                console.log("Encountered an error! [" + error + "]")
                alert("Request Failed: System error or you may not have enough privileges")
                spinner.hide()
            });
        },

        formValidation: function () {
            root.error_message = ""
            let no_operator = []
            let isValid = true;
            root.showError = false
            for (element in root.custom_report) {
                if(root.custom_report[element].value != '' && root.custom_report[element].operator == '')
                {
                    root.showError = true
                    //fetch all error
                    if(root.custom_report[element].operator == '')
                    {
                        isValid = false
                        no_operator.push(element)
                    }
                }
            }
            root.no_operator = no_operator;
            //display error
            root.error_message = "Put operator/s on: " + no_operator ;
            return isValid
        },
        generate: function () {
            let temp_show_fields = []
            checked_fields.forEach(element => {
                let temp_index = {'field': element, label: element.replaceAll("_"," ")}
                temp_show_fields.push(temp_index)
            });
            root.STARK_report_fields = temp_show_fields;
            this.custom_report['STARK_report_fields'] = root.STARK_report_fields
            let report_payload = { STARK_User_Sessions: this.custom_report }
            if(root.formValidation())
            {
                loading_modal.show()
                STARK_User_Sessions_app.report(report_payload).then( function(data) {
                    root.listview_table = data[0];
                    root.temp_csv_link = data[2][0];
                    root.temp_pdf_link = data[2][1];
                    console.log("DONE! Retrieved report.");
                    loading_modal.hide()
                    root.showReport = true

                })
                .catch(function(error) {
                    console.log("Encountered an error! [" + error + "]")
                    loading_modal.hide()
                });
            }
        },
        download_report(file_type = "csv") {
            let link = "https://" + (file_type == "csv" ? root.temp_csv_link : root.temp_pdf_link)
            window.location.href = link
        },
        checkUncheck: function (checked) {
            arrCheckBoxes = document.getElementsByName('check_checkbox');
            for (var i = 0; i < arrCheckBoxes.length; i++)
            {
                arrCheckBoxes[i].checked = checked;
            }

            if(checked)
            {
                checked_fields = temp_checked_fields
            }
            else
            {
                checked_fields = []
            }
        },
    }
})

//for selecting individually, select all or uncheck all of checkboxes
var temp_checked_fields = ['Session_ID','Username','Sess_Start','TTL','Permissions',]
var checked_fields = ['Session_ID','Username','Sess_Start','TTL','Permissions',]

