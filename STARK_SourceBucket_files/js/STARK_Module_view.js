var root = new Vue({
    el: "#vue-root",
    data: {
        listview_table: '',
        STARK_Module: {
            'Module_Name': '',
            'sk': '',
            'Descriptive_Title': '',
            'Target': '',
            'Description': '',
            'Module_Group': '',
            'Is_Menu_Item': '',
            'Is_Enabled': '',
            'Icon': '',
            'Priority': '',
        },
        lists: {
            'Is_Menu_Item': [
                { value: true, text: 'Y' },
                { value: false, text: 'N' },
            ],
            'Is_Enabled': [
                { value: true, text: 'Y' },
                { value: false, text: 'N' },
            ],
            'Module_Group': [
            ],
        },
        list_status: {
            'Module_Group': 'empty'
        },
        visibility: 'hidden',
        next_token: '',
        next_disabled: true,
        prev_token: '',
        prev_disabled: true,
        page_token_map: {1: ''},
        curr_page: 1

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

            let data = { STARK_Module: this.STARK_Module }

            STARK_Module_app.add(data).then( function(data) {
                console.log("VIEW: INSERTING DONE!");
                loading_modal.hide()
                window.location.href = "STARK_Module.html";
            }).catch(function(error) {
                console.log("Encountered an error! [" + error + "]")
                alert("Request Failed: System error or you may not have enough privileges")
                loading_modal.hide()
            });
        },

        delete: function () {
            loading_modal.show()
            console.log("VIEW: Deleting!")

            let data = { STARK_Module: this.STARK_Module }

            STARK_Module_app.delete(data).then( function(data) {
                console.log("VIEW: DELETE DONE!");
                console.log(data);
                loading_modal.hide()
                window.location.href = "STARK_Module.html";
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

            let data = { STARK_Module: this.STARK_Module }

            STARK_Module_app.update(data).then( function(data) {
                console.log("VIEW: UPDATING DONE!");
                console.log(data);
                loading_modal.hide()
                window.location.href = "STARK_Module.html";
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
            data['Module_Name'] = urlParams.get('Module_Name');

            if(data['Module_Name'] == null) {
                root.show();
            }
            else {
                loading_modal.show();
                console.log("VIEW: Getting!")

                STARK_Module_app.get(data).then( function(data) {
                    root.STARK_Module = data[0]; //We need 0, because API backed func always returns a list for now
                    // if(root.STARK_Module.Is_Enabled == true) {
                    //     root.STARK_Module.Is_Enabled = "Y"
                    // }
                    // else {
                    //     root.STARK_Module.Is_Enabled = "N"
                    // }
                    // if(root.STARK_Module.Is_Menu_Item == true) {
                    //     root.STARK_Module.Is_Menu_Item = "Y"
                    // }
                    // else {
                    //     root.STARK_Module.Is_Menu_Item = "N"
                    // }
                    root.STARK_Module.orig_Module_Name = root.STARK_Module.Module_Name;
                    root.lists.Module_Group = [  { value: root.STARK_Module.Module_Group, text: root.STARK_Module.Module_Group },]
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

            STARK_Module_app.list(payload).then( function(data) {
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
        list_Module_Group: function () {
            if (this.list_status.Module_Group == 'empty') {
                loading_modal.show();
                root.lists.Module_Group = []
 
                //FIXME: for now, generic list() is used. Can be optimized to use a list function that only retrieves specific columns
                STARK_Module_Groups_app.list().then( function(data) {
                    data['Items'].forEach(function(arrayItem) {
                        value = arrayItem['Group_Name']
                        text  = arrayItem['Group_Name']
                        root.lists.Module_Group.push({ value: value, text: text })
                    })
                    root.list_status.Module_Group = 'populated'
                    loading_modal.hide();
                }).catch(function(error) {
                    console.log("Encountered an error! [" + error + "]")
                    alert("Request Failed: System error or you may not have enough privileges")
                    loading_modal.hide();
                });
            }
        },
    }
})
