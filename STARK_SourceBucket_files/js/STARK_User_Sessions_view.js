var root = new Vue({
    el: "#vue-root",
    data: {
        metadata: {
            'Session_ID': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'String'
            },
            'Username':  {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'String'
            },
            'Sess_Start':  {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'String'
            },
            'TTL':  {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'String'
            },
            'Permissions':  {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'String'
            },
            'STARK_Report_Type': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'String',
                'state': null,
                'feedback': ''
            },
            'STARK_Chart_Type': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'String',
                'state': null,
                'feedback': ''
            },
            'STARK_X_Data_Source': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': '',
                'state': null,
                'feedback': ''
            },
            'STARK_Y_Data_Source': {
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
            'STARK_uploaded_s3_keys':{}
        },
        custom_report:{
            'Session_ID': {"operator": "", "value": "", "type":"S"},
            'Username':  {"operator": "", "value": "", "type":"S"},
            'Sess_Start':  {"operator": "", "value": "", "type":"S"},
            'TTL':  {"operator": "", "value": "", "type":"S"},
            'Permissions':  {"operator": "", "value": "", "type":"S"},
            'STARK_isReport':true,
            'STARK_report_fields':[],
            'STARK_Report_Type': '',
            'STARK_Chart_Type': '',
            'STARK_X_Data_Source': '',
            'STARK_Y_Data_Source': '',
            'STARK_sum_fields': [],
            'STARK_count_fields': [],
            'STARK_group_by_1': '',
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
            'STARK_Chart_Type': [
                { value: 'Bar Chart', text: 'Bar Chart' },
                { value: 'Pie Chart', text: 'Pie Chart' },
                { value: 'Line Chart', text: 'Line Chart' },
            ],
            'STARK_Report_Type': [
                { value: 'Tabular', text: 'Tabular' },
                { value: 'Graph', text: 'Graph' },
            ],
            'STARK_Data_Source': [
                { value: 'Session ID', text: 'Session ID' },
                { value: 'Username', text: 'Username' },
                { value: 'Sess Start', text: 'Sess Start' },
                { value: 'TTL', text: 'TTL' },
                { value: 'Permissions', text: 'Permissions' },
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
        all_selected: true,
        temp_checked_fields: ['Session ID','Username','Sess Start','TTL','Permissions',],
        checked_fields: ['Session ID','Username','Sess Start','TTL','Permissions',],
        showGraph: false,
        showChartFields: false,
        showXAxisFields: false,
        series_data: [],
        graphOption: [],
        fieldLabel: '',
        STARK_sum_fields: [],
        STARK_count_fields: [],
        STARK_group_by_1: '',
        Y_Data: [],
        showOperations: true,
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
            response = STARK.validate_form(root.metadata, root.STARK_User_Sessions)
            STARK_User_Sessions_app.add(data).then( function(data) {
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
                STARK.local_storage_delete_key('Listviews', 'STARK_User_Sessions');
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
                STARK.local_storage_delete_key('Listviews', 'STARK_User_Sessions');
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
                STARK.local_storage_delete_key('Listviews', 'STARK_User_Sessions');
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
                    root.STARK_User_Sessions = data["item"]; //We need 0, because API backed func always returns a list for now
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
            
            payload = []
            if (btn == 'next') {
                root.curr_page++;
                console.log(root.curr_page);
                payload['Next_Token'] = lv_token;
                root.prev_disabled = false;    
                root.next_disabled = true;
            }
            else if (btn == "prev") {
                root.curr_page--;
                if (root.curr_page > 1) {
                    root.prev_disabled = false
                }
                else {
                    root.prev_disabled = true
                    root.prev_token = ""
                }
            }

            var listview_data = STARK.get_local_storage_item('Listviews', 'STARK_User_Sessions')
            var fetch_from_db = false;
            console.log(listview_data)
            if(listview_data) {
                root.listview_table = listview_data[root.curr_page]
                root.next_token = listview_data['next_token'];

                if(listview_data[root.curr_page + 1]) {
                    root.next_disabled = false
                }
                if(root.next_token != "null") {
                    fetch_from_db = true
                }

                spinner.hide()
            }
            else {
                fetch_from_db = true
            }

            if(fetch_from_db) {

                STARK_User_Sessions_app.list(payload).then( function(data) {
                    token = data['Next_Token'];
                    root.listview_table = data['Items'];
                    var data_to_store = {}
                    data_to_store[root.curr_page] = data['Items']
                    data_to_store['next_token'] = token
                    STARK.set_local_storage_item('Listviews', 'STARK_User_Sessions', data_to_store)
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
            if(root.custom_report.STARK_Report_Type == 'Tabular') {
                root.metadata['STARK_Chart_Type'].required = false
                root.metadata['STARK_X_Data_Source'].required = false
                root.metadata['STARK_Y_Data_Source'].required = false
                if(root.custom_report.STARK_group_by_1 != '')
                {
                    root.showOperations = false
                }
            }
            else {
                root.metadata['STARK_Chart_Type'].required = true
                root.metadata['STARK_X_Data_Source'].required = true
                root.metadata['STARK_Y_Data_Source'].required = true
            }
            response = STARK.validate_form(root.metadata, root.custom_report)
            this.metadata = response['validation_properties']
            // console.log(response['is_valid_form'])
            if(response['is_valid_form']) {
                if(root.custom_report.STARK_Report_Type == 'Graph') {
                    root.showGraph = true
                }

                root.custom_report['STARK_report_fields'] = root.checked_fields
                let report_payload = { STARK_User_Sessions: root.custom_report }
                if(root.formValidation())
                {
                    loading_modal.show()
                    STARK_User_Sessions_app.report(report_payload).then( function(data) {
                        root.listview_table = data[0];
                        if(root.listview_table.length > 0) {
                            root.STARK_report_fields = Object.keys(root.listview_table[0])
                            if(root.custom_report.STARK_Report_Type == 'Tabular') {
                                root.temp_csv_link = data[1];
                                root.temp_pdf_link = data[2];
                            }
                        }
                        console.log("DONE! Retrieved report.");
                        loading_modal.hide()
                        if(root.custom_report.STARK_Report_Type == 'Tabular') {
                            root.showReport = true
                        }
                        else {
                            if(root.listview_table.length > 0)
                            {   
                                var element = document.getElementById("chart-container");
                                element.style.backgroundColor = "#ffffff";
                                root.activate_graph_download()
                                X_Data = root.custom_report.STARK_X_Data_Source
                                Y_Data = root.custom_report.STARK_Y_Data_Source

                                X_Data_Source = []
                                Y_Data_Source = []
                                Data_Source_Series = []
                                data[0].forEach(function(arrayItem) {
                                    if(root.custom_report.STARK_Chart_Type == 'Pie Chart') {
                                        value  = arrayItem[Y_Data]
                                        text   = arrayItem[X_Data]
                                        Data_Source_Series.push({ value: value, name: text }) 
                                    }
                                    else {
                                        X_Data_Source.push(arrayItem[X_Data])
                                        Y_Data_Source.push(arrayItem[Y_Data])
                                    }
                                })
                                var subtext = root.conso_subtext()
                                if(root.custom_report.STARK_Chart_Type == 'Pie Chart') {
                                    root.pieChart(Data_Source_Series, subtext)
                                }
                                else if(root.custom_report.STARK_Chart_Type == 'Bar Chart') {
                                    root.barChart(X_Data_Source, Y_Data_Source, subtext)
                                }
                                else if(root.custom_report.STARK_Chart_Type == 'Line Chart') {
                                    root.lineChart(X_Data_Source, Y_Data_Source, subtext)
                                }
                            }
                        }

                    })
                    .catch(function(error) {
                        console.log("Encountered an error! [" + error + "]")
                        alert("Request Failed: System error or you may not have enough privileges")
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

        refresh_list () {
            root.listview_table = ''
            STARK.local_storage_delete_key('Listviews', 'STARK_User_Sessions'); //localStorage
            root.list()
        },

        //Charting ------------------------------------------------
        set_x_data_source: function (field) {
            X_Data_Source = (field).replace(/_/g," ")
            root.custom_report.STARK_X_Data_Source = X_Data_Source
        },

        set_y_data_source: function (field) {
            Y_Data_Source = (field).replace(/_/g," ")
            data = { value: Y_Data_Source, text: Y_Data_Source }
            if(document.querySelector('#'+field).checked == true) {
                (root.Y_Data).push(data)
            }
            else {
                (root.Y_Data).pop(data)
            }
            root.lists.STARK_Data_Source = root.Y_Data
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
                    text: 'User Sessions Report',
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
                },
                tooltip: {

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
                    text: 'User Sessions Report',
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
                },
                tooltip: {

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
                    text: 'User Sessions Report',
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
            if(root.custom_report.STARK_Chart_Type == 'Pie Chart') {
                root.showChartFields = true
                root.fieldLabel = 'Pie Data Source'
                // root.showXAxisFields = false
            }
            else if (root.custom_report.STARK_Chart_Type == 'Bar Chart' || root.custom_report.STARK_Chart_Type == 'Line Chart') {
                // root.showXAxisFields = true
                root.showChartFields = true
                root.fieldLabel = 'X Axis Data Source'
            } 

        },

        showChartWizard: function () {
            if(root.custom_report.STARK_Report_Type == 'Graph') {
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
    }
})

