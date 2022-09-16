var root = new Vue({
    el: "#vue-root",
    data: {
        metadata: {
            'Username': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': '',
                'state': null,
                'feedback': ''
            },
            'Permissions': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': '',
                'state': null,
                'feedback': ''
            },
            'Report_Type': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': '',
                'state': null,
                'feedback': ''
            },
            'Chart_Type': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': '',
                'state': null,
                'feedback': ''
            },
            'Data_Table': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': '',
                'state': null,
                'feedback': ''
            },
            'Data_Source': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': '',
                'state': null,
                'feedback': ''
            },
        },
        auth_config: { },
        auth_list: {
            'View': {'permission': 'User Permissions|View', 'allowed': false},
            'Add': {'permission': 'User Permissions|Add', 'allowed': false},
            'Delete': {'permission': 'User Permissions|Delete', 'allowed': false},
            'Edit': {'permission': 'User Permissions|Edit', 'allowed': false},
            'Report': {'permission': 'User Permissions|Report', 'allowed': false}
        },
        STARK_report_fields: [],
        listview_table: '',
        STARK_User_Permissions: {
            'Username': '',
            'sk': '',
            'Permissions': '',
        },
        custom_report:{
            'Username': {"operator": "", "value": "", "type":"S"},
            'Permissions':  {"operator": "", "value": "", "type":"S"},
            'STARK_isReport':true,
            'STARK_report_fields':[],
            'Report_Type': '',
            'Chart_Type': '',
            'Data_Source': '',
        },
        lists: {
            'Permissions': [
            ],
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
            'Chart_Type': [
                { value: 'Bar Chart', text: 'Bar Chart' },
                { value: 'Pie Chart', text: 'Pie Chart' },
                { value: 'Line Chart', text: 'Line Chart' },
            ],
            'Report_Type': [
                { value: 'Tabular', text: 'Tabular' },
                { value: 'Graph', text: 'Graph' },
            ],
            'Data_Source': [
                { value: 'Username', text: 'Username' },
                { value: 'Permissions', text: 'Permissions' },
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
        showReport: false,
        object_url_prefix: "",
        temp_csv_link: "",
        temp_pdf_link: "",
        showError: false,
        no_operator: [],
        error_message: '',
        authFailure: false,
        authTry: false,
        all_selected: true,
        temp_checked_fields: ['Username','Permissions',],
        checked_fields: ['Username','Permissions',],
        search:{
            'Permissions': '',
        },
        showGraph: false,
        showChartFields: false,
        showXAxisFields: false,
        series_data: [],
        graphOption: [],
        fieldLabel: '',

    },
    methods: {

        show: function () {
            this.visibility = 'visible';
        },

        hide: function () {
            this.visibility = 'hidden';
        },

        add: function () {
            console.log("VIEW: Inserting!")
            this.STARK_User_Permissions.Permissions = (root.multi_select_values.Permissions.sort()).join(', ')																					
            response = STARK.validate_form(root.metadata, root.STARK_User_Permissions)
            this.metadata = response['new_metadata']
            if(response['is_valid_form']) {
                loading_modal.show()
													   
                let data = { STARK_User_Permissions: this.STARK_User_Permissions }
                
                STARK_User_Permissions_app.add(data).then( function(data) {
                    loading_modal.hide()
                    if(data != "OK")
                    {
                        for (var key in data) {
                            if (data.hasOwnProperty(key)) {
                                root.metadata[key]['state'] = false
                                root.metadata[key]['feedback'] = data[key]
                            }
                        }
                        return false
                    }
                    console.log("VIEW: INSERTING DONE!");
                    STARK.local_storage_delete_key('Listviews', 'STARK_User_Permissions'); 
                    window.location.href = "STARK_User_Permissions.html";
                }).catch(function(error) {
                    console.log("Encountered an error! [" + error + "]")
                    alert("Request Failed: System error or you may not have enough privileges")
                    loading_modal.hide()
                });
            }
        },

        delete: function () {
            loading_modal.show()
            console.log("VIEW: Deleting!")

            let data = { STARK_User_Permissions: this.STARK_User_Permissions }

            STARK_User_Permissions_app.delete(data).then( function(data) {
                console.log("VIEW: DELETE DONE!");
                STARK.local_storage_delete_key('Listviews', 'STARK_User_Permissions');
                console.log(data);
                loading_modal.hide()
                window.location.href = "STARK_User_Permissions.html";
            })
            .catch(function(error) {
                console.log("Encountered an error! [" + error + "]")
                alert("Request Failed: System error or you may not have enough privileges")
                loading_modal.hide()
            });
        },

        update: function () {
            console.log("VIEW: Updating!")
            this.STARK_User_Permissions.Permissions = (root.multi_select_values.Permissions.sort()).join(', ')																		
            response = STARK.validate_form(root.metadata, root.STARK_User_Permissions)
            this.metadata = response['new_metadata']
            if(response['is_valid_form']) {
                loading_modal.show()	

                let data = { STARK_User_Permissions: this.STARK_User_Permissions }

                STARK_User_Permissions_app.update(data).then( function(data) {
                    console.log(data);
                    loading_modal.hide()
                    if(data != "OK")
                    {
                        for (var key in data) {
                            if (data.hasOwnProperty(key)) {
                                root.metadata[key]['state'] = false
                                root.metadata[key]['feedback'] = data[key]
                            }
                        }
                        return false
                    }
                    console.log("VIEW: UPDATING DONE!");
                    STARK.local_storage_delete_key('Listviews', 'STARK_User_Permissions');
                    window.location.href = "STARK_User_Permissions.html";
                })
                .catch(function(error) {
                    console.log("Encountered an error! [" + error + "]")
                    alert("Request Failed: System error or you may not have enough privileges")
                    loading_modal.hide()
                });
            }
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
                    root.STARK_User_Permissions = data["item"]; //We need 0, because API backed func always returns a list for now
                    root.STARK_User_Permissions.orig_Username = root.STARK_User_Permissions.Username;
					permission_list = root.STARK_User_Permissions.Permissions 
                    root.multi_select_values.Permissions = (root.STARK_User_Permissions.Permissions.split(', ')).sort()		
                    root.list_Permissions()														
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

            var listview_data = STARK.get_local_storage_item('Listviews', 'STARK_User_Permissions')
            var fetch_from_db = false;
            console.log(listview_data)
            if(listview_data) {
                root.listview_table = listview_data[root.curr_page]
                root.next_token = listview_data['next_token'];
                spinner.hide()
            }
            else {
                fetch_from_db = true
            }

            if(fetch_from_db) {

                STARK_User_Permissions_app.list(payload).then( function(data) {
                    console.log(data)
                    for (let x = 0; x < (data['Items']).length; x++) {
                        data['Items'][x]['Permissions'] = ((data['Items'][x]['Permissions'].split(', ')).sort()).join(', ')      
                    }
                    token = data['Next_Token'];
                    root.listview_table = data['Items'];
                    var data_to_store = {}
                    data_to_store[root.curr_page] = data['Items']
                    data_to_store['next_token'] = token
                    STARK.set_local_storage_item('Listviews', 'STARK_User_Permissions', data_to_store)
                    console.log("DONE! Retrieved list.");
                    spinner.hide()

                    if (token != "null") {
                        root.next_disabled = false;
                        root.next_token = token;
                    }
                    else {
                        root.next_disabled = true;
                    }
                    console.log(root.listview_table)
                })
                .catch(function(error) {
                    console.log("Encountered an error! [" + error + "]")
                    alert("Request Failed: System error or you may not have enough privileges")
                    spinner.hide()
                });
            }
        },

        refresh_list () {
            root.listview_table = ''
            STARK.local_storage_delete_key('Listviews', 'STARK_User_Permissions'); //localStorage
            root.list()
        },

        list_Permissions: function () {
            if (this.list_status.Permissions == 'empty') {
                loading_modal.show();
                root.lists.Permissions = []

                //FIXME: for now, generic list() is used. Can be optimized to use a list function that only retrieves specific columns
                fields = ['Module_Name', 'Module_Name']
                STARK_Module_app.get_fields(fields).then( function(data) {
                    data.forEach(function(arrayItem) {
                        value = arrayItem['Module_Name']
                        text  = arrayItem['Module_Name']
                        root.lists.Permissions.push({ value: value, text: text })  
                    })

                    root.list_status.Permissions = 'populated'
                    loading_modal.hide();
                }).catch(function(error) {
                    console.log("Encountered an error! [" + error + "]")
                    alert("Request Failed: System error or you may not have enough privileges")
                    loading_modal.hide();
                });
            }
        },

        tag_display_text: function (tag) {
            if((this.lists.Permissions).length !== 0)
            {
                var index = this.lists.Permissions.findIndex(opt => tag == opt.value)
                return this.lists.Permissions[index].text
            }
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
            if(root.custom_report.Report_Type == 'Tabular') {
                root.metadata['Chart_Type'].required = false
                root.metadata['Data_Source'].required = false
            }
            else {
                root.metadata['Chart_Type'].required = true
                root.metadata['Data_Source'].required = true
            }
            response = STARK.validate_form(root.metadata, root.custom_report)
            this.metadata = response['new_metadata']
            // console.log(response['is_valid_form'])
            if(response['is_valid_form']) {
                if(root.custom_report.Report_Type == 'Graph') {
                    root.showGraph = true
                }
                let temp_show_fields = []
                root.checked_fields.forEach(element => {
                    let temp_index = {'field': element, label: element.replaceAll("_"," ")}
                    temp_show_fields.push(temp_index)
                });
                root.STARK_report_fields = temp_show_fields;
                this.custom_report['STARK_report_fields'] = root.STARK_report_fields
                let report_payload = { STARK_User_Permissions: this.custom_report }
                if(root.formValidation())
                {
                    loading_modal.show()
                    STARK_User_Permissions_app.report(report_payload).then( function(data) {
                        root.listview_table = data[0];
                        root.temp_csv_link = data[2][0];
                        root.temp_pdf_link = data[2][1];
                        console.log("DONE! Retrieved report.");
                        loading_modal.hide()
                        if(root.custom_report.Report_Type == 'Tabular') {
                            root.showReport = true
                        }
                        else {
                            root.activate_graph_download()
                            Data_Source = (root.custom_report.Data_Source).replace(/ /g,"_")
                            // root.get_all_data_source(Data_Source)
                            // console.log('root.a_All_Data_Source')
                            // console.log(Object(root.a_All_Data_Source))

                            All_Data_Source = []
                            data[0].forEach(function(arrayItem) {
                                All_Data_Source.push(arrayItem[Data_Source])
                            })

                            //List of Unique Customer Type
                            Data_Source_Series = []
                            Data_Source_Series = All_Data_Source.filter(root.uniqueArr);
                            // console.log('Data_Source_Series')
                            // console.log(Data_Source_Series)


                            if(root.custom_report.Chart_Type == 'Pie Chart') {
                                //Check Occurrence per Data Source for Pie Chart
                                Y_Data_Source_Series = []
                                Data_Source_Series.forEach(element => {
                                    value  = root.checkOccurrence(All_Data_Source, element)
                                    text   = element
                                    Y_Data_Source_Series.push({ value: value, name: text }) 
                                });
                            } else {

                                // Check Occurrence per Data Source
                                Y_Data_Source_Series = []
                                Data_Source_Series.forEach(element => {
                                    value  = root.checkOccurrence(All_Data_Source, element)
                                    // text   = element
                                    Y_Data_Source_Series.push(value) 
                                });
                            }

                            var subtext = root.conso_subtext()


                            if(root.custom_report.Chart_Type == 'Pie Chart') {
                                // console.log('Pie')
                                root.pieChart(Y_Data_Source_Series, subtext)
                            }
                            else if(root.custom_report.Chart_Type == 'Bar Chart') {
                                // console.log('Bar')
                                root.barChart(Data_Source_Series, Y_Data_Source_Series, subtext)
                            }
                            else if(root.custom_report.Chart_Type == 'Line Chart') {
                                // console.log('Line')
                                root.lineChart(Data_Source_Series, Y_Data_Source_Series, subtext)
                            }

                        }

                    })
                    .catch(function(error) {
                        console.log("Encountered an error! [" + error + "]")
                        loading_modal.hide()
                    });
                }
            }
        },
        download_report(file_type = "csv") {
            let link = "https://" + (file_type == "csv" ? root.temp_csv_link : root.temp_pdf_link)
            window.location.href = link
        },
        toggle_all(checked) {
            root.checked_fields = checked ? root.temp_checked_fields.slice() : []
            root.all_selected = checked
        },
        onOptionClick({ option, addTag }, reference) {
            addTag(option.value)
            this.search[reference] = ''
            this.$refs[reference].show(true)
        },

        //Charting ------------------------------------------------
        checkOccurrence: function (array, element) {
            counter = 0;
            for (item of array.flat()) {

                if (typeof item === "string") {
                    newItem = item.toLowerCase();
                    newElement = element.toLowerCase();
                    if (newItem == newElement) {
                        counter++;
                    }
                } else {
                    if (item == element) {
                        counter++;
                    }
                }
            }
            return counter;
        },

        uniqueArr: function(value, index, self) {
            return self.indexOf(value) === index;
        },

        barChart: function (x_data, y_data, subtext) {
            var dom = document.getElementById('chart-container')
            var myChart = echarts.init(dom, null, {
                    renderer: 'canvas',
                    useDirtyRect: false
            });

            var app = {};
            var option;

            option = {
                title: {
                    text: 'Customer Report',
                    subtext: '',
                    right: 'center',
                    top: 20,
                    bottom: 20
                },
                xAxis: {
                    type: 'category',
                    data: []
                },
                yAxis: {
                    type: 'value'
                },
                series: [
                    {
                        data: [],
                        type: 'bar'
                    }
                ],
                grid: {
                    y: 120,
                    y2: 60,
                }
            };
            option.xAxis.data = x_data
            option.series[0].data = y_data
            option.title.subtext = subtext

            if (option && typeof option === 'object') {
                myChart.setOption(option);
            }

            window.addEventListener('resize', myChart.resize);
        },

        lineChart: function (x_data, y_data, subtext) {
            //START - Line Chart Components
            var dom = document.getElementById('chart-container')
            var myChart = echarts.init(dom, null, {
                    renderer: 'canvas',
                    useDirtyRect: false
            });

            var app = {};
            var option;

            option = {
                title: {
                    text: 'Customer Report',
                    subtext: '',
                    right: 'center',
                    top: 20,
                    bottom: 20
                },
                xAxis: {
                    type: 'category',
                    data: []
                },
                yAxis: {
                    type: 'value'
                },
                series: [
                    {
                        data: [],
                        type: 'line'
                    }
                ],
                grid: {
                    y: 120,
                    y2: 60,
                }
            };
            option.xAxis.data = x_data
            option.series[0].data = y_data
            option.title.subtext = subtext

            if (option && typeof option === 'object') {
                myChart.setOption(option);
            }

            window.addEventListener('resize', myChart.resize);
        //END - Line Chart Components
        },

        pieChart: function (y_data, subtext) {
            //START - Pie Chart Components
            var dom = document.getElementById('chart-container');
            var myChart = echarts.init(dom, null, {
                    renderer: 'canvas',
                    useDirtyRect: false
            });

            var app = {};
            var option;

            option = {
                series: [
                    {
                        name: 'Access From',
                        type: 'pie',
                        radius: '60%',
                        data: [],
                        emphasis: {
                            itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                            }
                        }
                    }
                ],
                title: {
                    text: 'Customer Report',
                    subtext: '',
                    right: 'center',
                    top: 20,
                    bottom: 20
                },
                tooltip: {
                    trigger: 'item'
                },
                legend: {
                    orient: 'vertical',
                    left: 'left',

                },
                grid: {
                    y: 120,
                    y2: 60,
                }
            };
            //Pass new value for data series
            option.series[0].data = y_data
            option.title.subtext = subtext

            if (option && typeof option === 'object') {
                myChart.setOption(option);
            }

            window.addEventListener('resize', myChart.resize);
            //END - Pie Chart Components
        },

        activate_graph_download: function () {
            window.html2canvas = html2canvas
            window.jsPDF = window.jspdf.jsPDF
            filename = STARK.create_UUID()

            const btnExportHTML = document.getElementById("exportByHTML")
            btnExportHTML.addEventListener("click", async () => {
                console.log("exporting...");
                try {
                    const doc = new jsPDF({
                        unit: "px",
                        orientation: "l",
                        hotfixes: ["px_scaling"]
                    });

                    const canvas = await html2canvas(document.querySelector("#chart-container"))
                    const img = await root.loadImage(canvas.toDataURL())
                    doc.addImage(img.src, 'PNG', 50, 100, 1000, 500)
                    await doc.save(filename)
                } catch (e) {
                    console.error("failed to export", e);
                }
                console.log("exported");
            })
        },

        loadImage: function(src) {
            return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = src;
            });
        },

        showFields: function () {
            // console.log(root.custom_report.Report_Type)
            if(root.custom_report.Chart_Type == 'Pie Chart') {
                root.showChartFields = true
                root.fieldLabel = 'Pie Data Source'
                // root.showXAxisFields = false
            }
            else if (root.custom_report.Chart_Type == 'Bar Chart' || root.custom_report.Chart_Type == 'Line Chart') {
                // root.showXAxisFields = true
                root.showChartFields = true
                root.fieldLabel = 'X Axis Data Source'
            } 

        },

        showChartWizard: function () {
            if(root.custom_report.Report_Type == 'Graph') {
                root.showChartFields = true
            }
            else {
                root.showChartFields = false
            }
        },

        conso_subtext: function () {
            conso_subtext = ''
            subtext_length = 0
            subtext = ''
            for (element in root.custom_report) {

                if(root.custom_report[element].operator != '' && root.custom_report[element].operator != undefined)
                {
                    field = element.replace("_", " ")
                    operator = (root.custom_report[element].operator).replace("_", " ")
                    val = root.custom_report[element].value
                    subtext = field + " " + operator + " " + val + " | "
                    conso_subtext = conso_subtext.concat(subtext)

                    subtext_length += subtext.length
                    if(subtext_length >= 100) {
                        conso_subtext += "\n"
                        subtext_length = 0
                    }
                }
            }
            return conso_subtext
        }
    },
    computed: {
        Permissions_criteria() {
            console.log(this.search['Permissions'].trim().toLowerCase())
            return this.search['Permissions'].trim().toLowerCase()
        },
        Permissions() {
            const Permissions_criteria = this.Permissions_criteria
            // Filter out already selected options
            const options = this.lists.Permissions.filter(opt => this.multi_select_values.Permissions.indexOf(opt.value) === -1)
            if (Permissions_criteria) {
            // Show only options that match Permissions_criteria
            return options.filter(opt => (opt.text).toLowerCase().indexOf(Permissions_criteria) > -1);
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

//for selecting individually, select all or uncheck all of checkboxes
var temp_checked_fields = ['Username','Permissions',]
var checked_fields = ['Username','Permissions',]
