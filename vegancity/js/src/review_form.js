'use strict';

var $ = require('jquery');

function init() {
    $(document).ready(function () {
        /*
          if there are no vegan dishes in the dropdown box,
          hide the dropdown box, and hide the text that says
          "if unlisted"
        */
        if ($("div.vegan-dish-choices select option").length <= 1) {
            $("div.vegan-dish-choices").hide();
        }
    });
}

module.exports = {
    init: init
};
