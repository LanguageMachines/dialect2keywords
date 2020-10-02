(function (window, $, undefined) {

  // List of colors corresponding to the given confidence values
  var colors = {
    '0' : '#ffa9a9',
    '1' : '#ffbda9',
    '2' : '#ffe5a9',
    '3' : '#e8ffa9',
    '4' : '#c8ffa9',
    '5' : '#85fda9',
  };

  // Function called on load to color the boxes of the words
  $('td.estimate').each(function () {
    // Set the backgound colors of the predicted keywords based on their confidences
    $(this).css('background-color', colors[$(this).data('confidence')]);
  });

  // Function that is triggered when the box of a keyword is clicked
  $('.acceptWord').click(function () {
    // The clicked keyword is given to the input area that is on the 3rd column of the table
    $(this).parent().children('td').eq(3).find('input').val($(this).text().trim());
    // Rest of the function changes the design based on the selection of the user
    if (!$(this).hasClass('accepted-word')) {
      $(this).addClass('accepted-word');
    } else {
      $(this).removeClass('accepted-word');
    }
    // Remove the 'accepted word style' from the rest of the columns
    $(this).next('td').removeClass('accepted-word');
    $(this).next('td').next('td').removeClass('accepted-word');
    $(this).prev('td').removeClass('accepted-word');
    $(this).prev('td').prev('td').removeClass('accepted-word');
  });

  // The previous inputs should be assigned back to the input
  // So that Django reads and saves them alongside the new inputs
  $('input.user-input').each(function (i, item) {
    $(item).val(window.prevUserInputs[i]);
  });

})(window, window.jQuery);
