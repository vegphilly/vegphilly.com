var $ = require('jquery');

function init() {
    $(document).ready(function() {
      $(".gear").click(function(){
        $(".profile-menu").toggleClass("open");
      });
    });
}

module.exports = {
    init: init
};
