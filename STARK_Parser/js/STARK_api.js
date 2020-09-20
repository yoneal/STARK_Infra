var root = new Vue({
    el: "#vue-root",
    data: {
        form: {
            data_model: `__STARK_project_name__: 
Customer:
    pk: Customer ID
    data:
        - Customer Name: string
        - Gender: [ Male, Female, LGBTQ+ ]
        - Join Date: date
        - Remarks: multi-line-string
Sales Agent:
    pk: Employee ID
    data:
        - First Name: string
        - Last Name: string
        - Sex: [ "Yes", "No", "HR is calling" ]
        - Hiring Date: string
        - Salary: string
        - TIN: string
Item:
    pk: Product Code
    data:
        - Title: string
        - Category: string
        - Description: string
Document:
    pk: Document ID
    data:
        - Title: string
        - Revision: string
        - Description: string`,
        },
        api_key: '',
        deploy_visibility: 'hidden',
        model_readonly: false,
        loading_message: '',
        visibility: 'visible',
        spinner_display: 'block',
        success_message: 'STARK Parser is idle',
        msg_counter: 0,
        ui_visibility: 'block'
    },
    methods:{
        send_to_STARK: function () {
            root.success_message = ''
            root.loading_message = "STARK is parsing your YAML model..."
            root.spinner_show();

            let data = {
                data_model: this.form.data_model
            }

            let fetchData = {
                mode: 'cors',
                body: JSON.stringify(data),
                headers: { "Content-Type": "application/json" },
                method: "POST",
            }

            console.log(fetchData);

            fetch(STARK.parser_url, fetchData)
            .then( function(response) {
                //FIX-ME:
                //Error handling here should just be for network-related failiures
                //Actual server errors should be handled properly by the API, giving back useful error messages and status codes.
                if (!response.ok) {
                    console.log(response)
                    throw Error(response.statusText);
                }
                return response;
            })
            .then((response) => response.json())
            .then( function(data) {
                root.loading_message = ""
                root.spinner_hide();

                console.log("Received Response")
                console.log(data)
                if (data == "Code:NoProjectName") {
                    console.log("Error Code")
                    root.success_message = "Please enter a project name in the \"__STARK_project_name__\" attribute below"

                }else {
                    console.log("Success")
                    console.log("DONE!");

                    root.success_message = "Nice! Your YAML looks valid according to the STARK Parser.<br>Click \"Deploy\" to launch your serverless system!"

                    root.deploy_visibility = 'visible';
                    root.model_readonly = true;
                }
            })
            .catch(function(error) {
                root.loading_message = ""
                root.spinner_hide();
                root.success_message = "Sorry, your YAML is invalid. Make sure it conforms to STARK syntax, then try again. "
            });
        },
        deploy_STARK: function () {
            root.success_message = ''
            root.loading_message = "STARK is deploying your system...." 
            root.spinner_show();

            root.deploy_visibility = 'hidden';
            root.ui_visibility = 'none';

            let data = {
                data_model: this.form.data_model
            }

            let fetchData = {
                mode: 'cors',
                body: JSON.stringify(data),
                headers: { "Content-Type": "application/json" },
                method: "POST",
            }

            console.log(fetchData);

            fetch(STARK.deploy_url, fetchData)
            .then( function(response) {
                if (!response.ok) {
                    console.log(response)
                    throw Error(response.statusText);
                }
                return response;
            })
            .then((response) => response.json())
            .then( function(data) {
                console.log("DONE!");
                console.log(data);

                //Comm loop:
                //  data will contain an index 'retry' which is bool. True means we should call root.deploy_check()
                //  root.deploy_check() will initiate a comm loop with lambda until it gets a data[retry] = False
                //  While it is looping, each communication also contains `status` and `message` aside from `retry`.
                //  We should display `status` and `message` to the user.
                root.msg_counter += 1;

                if(data['retry'] == true) {
                    root.deploy_check();
                }
                else {
                    //Failed:
                    //This means CF Stack execution failed outright.
                    console.log("CF Stack Failure returned by Lambda!");
                    root.loading_message = ""
                    root.spinner_hide();
                    root.success_message = data['message'];
                }

            })
            .catch(function(error) {
                console.log("CF Stack Failure - 500 Error Code");
                root.loading_message = ""
                root.spinner_hide();
                root.success_message = "Deploy failed: We encountered an internal error. It's not you, it's us!<br>";            
            });
        },
        deploy_check: function () {

            let data = {
                data_model: this.form.data_model
            }

            let fetchData = {
                mode: 'cors',
                body: JSON.stringify(data),
                headers: { "Content-Type": "application/json" },
                method: "POST",
            }

            console.log(fetchData);

            fetch(STARK.deploy_check_url, fetchData)
            .then( function(response) {
                if (!response.ok) {
                    console.log(response)
                    throw Error(response.statusText);
                }
                return response;
            })
            .then((response) => response.json())
            .then( function(data) {
                console.log("DONE!");
                console.log(data);

                //Comm loop:
                //  data will contain an index 'retry' which is bool. True means we should call root.deploy_check() again.
                //  While it is looping, each communication also contains `status` and `message` aside from `retry`.
                //  We should display `status` and `message` to the user.
                if(data['retry'] == true) {

                    if (root.msg_counter == 1) {
                        root.loading_message = "Look at you, testing out next-gen serverless tech! BIG BRAIN MOVE!"
                    }
                    else if (root.msg_counter == 2) {
                        root.loading_message = "DID YOU KNOW: Trying out STARK proves you are a person of exquisite taste and sophistication. (True story)"
                    }
                    else if (root.msg_counter == 3) {
                        root.loading_message = "It won't be long now dawg, we're almost done!"
                    }
                    else {
                        root.loading_message = "Hmmm... we're taking a bit longer than usual... must be traffic!"
                    }
    
                    root.msg_counter += 1;
                    root.deploy_check()
                }
                else {
                    //Success:
                    //Data should contain the S3 bucket URL for website hosting that was created for us.
                    //We'll show a link to the user, for clicking and fun.
                    console.log("Success! Here's your new system URL: " + data['url']);
                    root.loading_message = ""
                    root.spinner_hide();
                    root.success_message = "Success! Here's your new system URL: <a href='" + data['url'] + "'>" + data['url'] + "</a>";
                }
            })
            .catch(function(error) {
                
            });

        },

        spinner_show: function () {
            console.log("trying to show");
            this.visibility = 'visible';
        },
        spinner_hide: function () {
            console.log("trying to hide");
            this.visibility = 'hidden';
        },


    }
})

root.spinner_hide();