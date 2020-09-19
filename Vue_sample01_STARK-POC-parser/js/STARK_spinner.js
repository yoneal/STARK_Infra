var spinner = new Vue({
    el: "#loading-spinner",
    data: {
        visibility: 'visible',
    },
    methods: {
        show: function () {
            console.log("trying to show");
            this.visibility = 'visible';
        },
        hide: function () {
            console.log("trying to hide");
            this.visibility = 'hidden';
        }
    }
})
