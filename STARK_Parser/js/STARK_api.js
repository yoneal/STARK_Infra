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
        - Preferred Customer: yes-no
        - Customer Type: 
            type: relationship
            has_one: Customer Type
            value: Customer Type
            display: Customer Type
        - Remarks: multi-line-string
Item:
    pk: Product Code
    data:
        - Title: string
        - In Stock:
            type: int-spinner
            min: 5
            max: 50
        - Weight in kg:
            type: decimal-spinner
            wrap: no-wrap
        - Categories:
            type: tags
            limit: 3
            values: [ "Regular", "Deluxe", "Premium" ]
        - Rating:
            type: rating
            max: 10
        - Variations Available:
            type: multiple choice
            values: [ "Small", "Medium", "Large", "XL"]
        - Description: multi-line-string
        - Packaging Type:
            type: radio button
            values: [ "Traditional Box", "Standard Cardboard", "Eco-Friendly" ]
        - Max Discount Rate:
            type: radio bar
            values: [ "None", "10%", "15%", "20%", "25%" ]
        - Last Update: time
Customer Type:
    pk: Customer Type
    data:
        - Description: multi-line-string
Document:
    pk: Document ID
    data:
        - Title: string
        - Revision: int
        - Numerical Code: number
        - Description: string`,
        },
        api_key: '',
        current_stack: 0,
        deploy_time_end: '',
        deploy_time_start: '',
        deploy_visibility: 'hidden',
        loading_message: '',
        model_readonly: false,
        msg_counter: 0,
        spinner_display: 'block',
        success_message: 'Welcome to STARK: Serverless Transformation and Acceleration Resource Kit.<br> The STARK Parser is idle',
        ui_visibility: 'block',
        visibility: 'visible',
        wait_counter: 0,
        wait_limit: 12
    },
    methods:{
        send_to_STARK: function () {
            root.success_message = ''
            root.loading_message = "STARK is parsing your YAML model..."
            root.spinner_show();

            let data = {
                data_model: this.form.data_model
            }

            console.log(JSON.stringify(data))
            
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

            let datetime = new Date()
            root.deploy_time_start = datetime.getHours() + ":" + datetime.getMinutes() + ":" + datetime.getSeconds()

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
                root.success_message = "Deploy failed: STARK encountered an internal error. It's not you, it's us!<br>(You can try again or come back later to see if this error persists)";            
            });
        },
        deploy_check: function () {

            let data = {
                data_model: this.form.data_model,
                current_stack: root.current_stack
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

                //Status tracker:
                //  current_stack tracks which of the three stacks we are currently tracking:
                //  0 - CI/CD Pipeline stack
                //  1 - Bootstrapper stack
                //  2 - Main application stack
                const stack_messages = [
                    'Deployment 1 of 3: Your CI/CD Pipeline... <br>',
                    'Deployment 2 of 3: System Bootstrapper...<br>',
                    'Deployment 3 of 3: Your main application...<br>'
                ]
                root.current_stack = data['current_stack']
                root.loading_message = stack_messages[root.current_stack]

                //Comm loop:
                //  data will contain an index 'retry' which is bool. True means we should call root.deploy_check() again.
                //  While it is looping, each communication also contains `status` and `message` aside from `retry`.
                //  We should display `status` and `message` to the user.
                //  There's also a special status to track - "STACK_NOT_FOUND" - that means we should decide here whether to
                //  retry again (i.e., wait to see if the stack eventually gets created), or if we've waited enough and there's
                //  probably an internal error that prevented the stack from being created
                if(data['result'] == "STACK_NOT_FOUND") {
                    root.wait_counter +=1
                    if (root.wait_counter > root.wait_limit) {
                        //We've waited enough, abort
                        data['retry'] = false
                        data['result'] = 'FAILED'
                        data['status'] = 'STACK NOT FOUND: Stack #' + root.current_stack
                    }
                }

                if(data['retry'] == true) {

                    if (root.msg_counter == 1) {
                        root.loading_message += "Look at you, testing out next-gen serverless tech! BIG BRAIN MOVE!"
                    }
                    else if (root.msg_counter == 2) {
                        root.loading_message += "DID YOU KNOW: Trying out STARK proves you are a person of exquisite taste and sophistication. (True story)"
                    }
                    else if (root.msg_counter == 3) {
                        root.loading_message += "Serverless is the most sustainable form of computing. Thanks for being a good friend to the environment!"
                    }
                    else if (root.msg_counter == 4) {
                        root.loading_message += "It won't be long now dawg, we're almost done!"
                    }
                    else {
                        root.loading_message += "Hmmm... we're taking a bit longer than usual... must be traffic!"
                    }
    
                    root.msg_counter += 1;
                    if(root.msg_counter > 5) {
                        //Just reset so we can cycle through the messages instead of looking like we're stuck
                        root.msg_counter = 1
                    }
                    root.deploy_check()
                }
                else if (data['result'] == "SUCCESS" && data['current_stack'] == 2 ) {
                    //Success:
                    //Data should contain the S3 bucket URL for website hosting that was created for us.
                    //We'll show a link to the user, for clicking and fun.
                    console.log("Success! Here's your new system URL: " + data['url']);

                    let datetime = new Date()
                    root.deploy_time_end = datetime.getHours() + ":" + datetime.getMinutes() + ":" + datetime.getSeconds()
        
                    root.loading_message = ""
                    root.spinner_hide();
                    root.success_message = "Success! Here's your new system URL: <a href='" + data['url'] + "'>" + data['url'] + "</a>";
                    root.success_message += "<br> Time start: " + root.deploy_time_start
                    root.success_message += "<br> Time end: " + root.deploy_time_end
                }
                else if (data['result'] == "FAILED") {
                    //This means CF Stack execution eventually failed.
                    console.log("CF Stack Execution failure...");
                    root.spinner_hide();
                    root.success_message = "Sorry, STARK failed to deploy due to an internal error. It's not you, it's us! {" +  data['status'] + "}";

                }
            })
            .catch(function(error) {
                console.log("CF Stack Failure - Deploy Check - 500 Error Code");
                root.loading_message = ""
                root.spinner_hide();
                root.success_message = "Deploy failed: STARK encountered an internal error. It's not you, it's us!<br>(You can try again or come back later to see if this error persists)";                
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