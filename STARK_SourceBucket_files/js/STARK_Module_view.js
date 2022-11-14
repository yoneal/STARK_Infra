var root = new Vue({
    el: "#vue-root",
    data: {
        metadata: {
            'Module_Name': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'String',
                'state': null,
                'feedback': ''
            },
            'Descriptive_Title': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'String',
                'state': null,
                'feedback': ''
            },
            'Target': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'String',
                'state': null,
                'feedback': ''
            },
            'Description': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'String',
                'state': null,
                'feedback': ''
            },
            'Module_Group': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'String',
                'state': null,
                'feedback': ''
            },
            'Is_Menu_Item': {
                'value': '',
                'required': false,
                'max_length': '',
                'data_type': 'String',
                'state': null,
                'feedback': ''
            },
            'Is_Enabled': {
                'value': '',
                'required': false,
                'max_length': '',
                'data_type': 'String',
                'state': null,
                'feedback': ''
            },
            'Icon': {
                'value': '',
                'required': false,
                'max_length': '',
                'data_type': 'String',
                'state': null,
                'feedback': ''
            },
            'Priority': {
                'value': '',
                'required': true,
                'max_length': '',
                'data_type': 'Number',
                'state': null,
                'feedback': ''
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
            'View': {'permission': 'System Modules|View', 'allowed': false},
            'Add': {'permission': 'System Modules|Add', 'allowed': false},
            'Delete': {'permission': 'System Modules|Delete', 'allowed': false},
            'Edit': {'permission': 'System Modules|Edit', 'allowed': false},
            'Report': {'permission': 'System Modules|Report', 'allowed': false}
        },
        STARK_report_fields: [],
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
            'STARK_uploaded_s3_keys':{}
        },
        custom_report:{
            'Module_Name': {"operator": "", "value": "", "type":"S"},
            'Descriptive_Title':  {"operator": "", "value": "", "type":"S"},
            'Target':  {"operator": "", "value": "", "type":"S"},
            'Description':  {"operator": "", "value": "", "type":"S"},
            'Module_Group':  {"operator": "", "value": "", "type":"S"},
            'Is_Menu_Item':  {"operator": "", "value": "", "type":"S"},
            'Is_Enabled':  {"operator": "", "value": "", "type":"S"},
            'Icon':  {"operator": "", "value": "", "type":"S"},
            'Priority':  {"operator": "", "value": "", "type":"S"},
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
                { value: 'Module Name', text: 'Module Name' },
                { value: 'Descriptive Title', text: 'Descriptive Title' },
                { value: 'Target', text: 'Target' },
                { value: 'Description', text: 'Description' },
                { value: 'Module Group', text: 'Module Group' },
                { value: 'Is Menu Item', text: 'Is Menu Item' },
                { value: 'Is Enabled', text: 'Is Enabled' },
                { value: 'Icon', text: 'Icon' },
                { value: 'Priority', text: 'Priority' },
            ],
        },
        list_status: {
            'Module_Group': 'empty'
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
        temp_checked_fields: ['Module Name','Descriptive Title','Target','Description','Module Group','Is Menu Item','Is Enabled','Icon','Priority',],
        checked_fields: ['Module Name','Descriptive Title','Target','Description','Module Group','Is Menu Item','Is Enabled','Icon','Priority',],
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
            console.log("VIEW: Inserting!")
            response = STARK.validate_form(root.metadata, root.STARK_Module)
            this.metadata = response['validation_properties']
            if(response['is_valid_form']) {
                loading_modal.show()

                let data = { STARK_Module: this.STARK_Module }

                STARK_Module_app.add(data).then( function(data) {
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
                    STARK.local_storage_delete_key('Listviews', 'STARK_Module'); 
                    window.location.href = "STARK_Module.html";
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

            let data = { STARK_Module: this.STARK_Module }

            STARK_Module_app.delete(data).then( function(data) {
                console.log("VIEW: DELETE DONE!");
                STARK.local_storage_delete_key('Listviews', 'STARK_Module'); 
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
            console.log("VIEW: Updating!")
            response = STARK.validate_form(root.metadata, root.STARK_Module)
            this.metadata = response['validation_properties']
            if(response['is_valid_form']) {
                loading_modal.show()

                let data = { STARK_Module: this.STARK_Module }

                STARK_Module_app.update(data).then( function(data) {
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
                    STARK.local_storage_delete_key('Listviews', 'STARK_Module'); 
                    window.location.href = "STARK_Module.html";
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
            data['Module_Name'] = urlParams.get('Module_Name');

            if(data['Module_Name'] == null) {
                root.show();
            }
            else {
                loading_modal.show();
                console.log("VIEW: Getting!")

                STARK_Module_app.get(data).then( function(data) {
                    root.STARK_Module = data["item"]; //We need 0, because API backed func always returns a list for now
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

            var listview_data = STARK.get_local_storage_item('Listviews', 'STARK_Module')
            var fetch_from_db = false;
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

                STARK_Module_app.list(payload).then( function(data) {
                    token = data['Next_Token'];
                    root.listview_table = data['Items'];
                    var data_to_store = {}
                    data_to_store[root.curr_page] = data['Items']
                    data_to_store['next_token'] = token
                    STARK.set_local_storage_item('Listviews', 'STARK_Module', data_to_store)
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
                let report_payload = { STARK_Module: root.custom_report }
                if(root.formValidation())
                {
                    loading_modal.show()
                    STARK_Module_app.report(report_payload).then( function(data) {
                        root.listview_table = data[0];
                        if(root.listview_table.length > 0) {
                            if(root.custom_report.STARK_Report_Type == 'Tabular') {
                                root.STARK_report_fields = root.checked_fields 
                                root.temp_csv_link = data[1];
                                root.temp_pdf_link = data[2];
                            } else {
                                root.STARK_report_fields = Object.keys(root.listview_table[0])
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
            STARK.local_storage_delete_key('Listviews', 'STARK_Module'); //localStorage
            root.list()
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
                    text: 'System Modules Report',
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
                    text: 'System Modules Report',
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
                    text: 'System Modules Report',
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
