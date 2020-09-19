var spinner = new Vue({
    el: "#loading-spinner",
    data: {
        visibility: 'visible'
    },
    methods: {
        show: function () {
            this.visibility = 'visible';
        },
        hide: function () {
            this.visibility = 'hidden';
        }
    }
})
