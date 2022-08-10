var root = new Vue({
    el: "#vue-root",
    data: {
        listview_table: '',
        STARK_User_Permissions: {
            'Username': '',
            'sk': '',
            'Permissions': '',
        },
        lists: {
            'Permissions': [
            ],
        },
        list_status: {
            'Permissions': 'empty',								   
        },
        multi_select_values: {
            'Permissions': [],
        },
		PermissionsVal: [],									  
        visibility: 'hidden',
        next_token: '',
        next_disabled: true,
        prev_token: '',
        prev_disabled: true,
        page_token_map: {1: ''},
        curr_page: 1,
        search:{
            'Permissions': '',
        },

    },
    methods: {

        show: function () {
            this.visibility = 'visible';
        },

        hide: function () {
            this.visibility = 'hidden';
        },

        add: function () {
													   
            this.STARK_User_Permissions.Permissions = root.multi_select_values.Permissions.join(', ')																					
			
            loading_modal.show()
            console.log("VIEW: Inserting!")

            let data = { STARK_User_Permissions: this.STARK_User_Permissions }
			

            STARK_User_Permissions_app.add(data).then( function(data) {
                console.log("VIEW: INSERTING DONE!");
                loading_modal.hide()
                window.location.href = "STARK_User_Permissions.html";
            }).catch(function(error) {
                console.log("Encountered an error! [" + error + "]")
                loading_modal.hide()
            });
        },

        delete: function () {
            loading_modal.show()
            console.log("VIEW: Deleting!")

            let data = { STARK_User_Permissions: this.STARK_User_Permissions }

            STARK_User_Permissions_app.delete(data).then( function(data) {
                console.log("VIEW: DELETE DONE!");
                console.log(data);
                loading_modal.hide()
                window.location.href = "STARK_User_Permissions.html";
            })
            .catch(function(error) {
                console.log("Encountered an error! [" + error + "]")
                loading_modal.hide()
            });
        },

        update: function () {
            loading_modal.show()
            console.log("VIEW: Updating!")

			this.STARK_User_Permissions.Permissions = root.multi_select_values.Permissions.join(', ')																		
            let data = { STARK_User_Permissions: this.STARK_User_Permissions }

            STARK_User_Permissions_app.update(data).then( function(data) {
                console.log("VIEW: UPDATING DONE!");
                console.log(data);
                loading_modal.hide()
                window.location.href = "STARK_User_Permissions.html";
            })
            .catch(function(error) {
                console.log("Encountered an error! [" + error + "]")
                loading_modal.hide()
            });
        },

        get: function () {
            const queryString = window.location.search;
            const urlParams = new URLSearchParams(queryString);
            //Get whatever params are needed here (pk, sk, filters...)
            data = {}
            data['Username'] = urlParams.get('Username');

            if(data['Username'] == null) {
                root.show();
            }
            else {
                loading_modal.show();
                console.log("VIEW: Getting!")

                STARK_User_Permissions_app.get(data).then( function(data) {
                    root.STARK_User_Permissions = data[0]; //We need 0, because API backed func always returns a list for now
                    root.STARK_User_Permissions.orig_Username = root.STARK_User_Permissions.Username;
					permission_list = root.STARK_User_Permissions.Permissions 
                    root.multi_select_values.Permissions = root.STARK_User_Permissions.Permissions.split(', ')																
                    console.log("VIEW: Retreived module data.")
                    root.show()
                    loading_modal.hide()
                })
                .catch(function(error) {
                    console.log("Encountered an error! [" + error + "]")
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

            STARK_User_Permissions_app.list(payload).then( function(data) {
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
                spinner.hide()
            });
        },

        list_Permissions: function () {
            if (this.list_status.Permissions == 'empty') {
                loading_modal.show();
                root.lists.Permissions = []

                //FIXME: for now, generic list() is used. Can be optimized to use a list function that only retrieves specific columns
                field = 'Module_Name'
                STARK_Module_app.get_field(field).then( function(data) {
                    data.forEach(function(arrayItem) {
                        value = arrayItem['Module_Name']
                        text  = arrayItem['Module_Name']
                        root.lists.Permissions.push(value)   
                        // console.log(root.lists.Permissions)    
                        
                    })

                    root.list_status.Permissions = 'populated'
                    loading_modal.hide();
                }).catch(function(error) {
                    console.log("Encountered an error! [" + error + "]")
                    loading_modal.hide();
                });
            }
        },
        onOptionClick({ option, addTag }, reference) {
            addTag(option)
            this.search[reference] = ''
            this.$refs[reference].show(true)
        },
    },
    computed: {
        Permissions_criteria() {
            console.log(this.search['Permissions'].trim().toLowerCase())
            return this.search['Permissions'].trim().toLowerCase()
        },
        Permissions() {
            const Permissions_criteria = this.Permissions_criteria
            // Filter out already selected options
            const options = this.lists.Permissions.filter(opt => this.multi_select_values.Permissions.indexOf(opt) === -1)
            if (Permissions_criteria) {
            // Show only options that match Permissions_criteria
            return options.filter(opt => opt.toLowerCase().indexOf(Permissions_criteria) > -1);
            }
            // Show all options available
            console.log(options)
            return options
        },
        Permissions_search_desc() {
            if (this.Permissions_criteria && this.Permissions.length === 0) {
            return 'There are no tags matching your search criteria'
            }
            return ''
        },
    }
})
