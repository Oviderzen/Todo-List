$(document).ready(function() {
  // Define the checkTask function
  function checkTask(id) {
    $.ajax({
      url: '/check_task/' + id + '/',
      type: 'POST',
      success: function(response) {
        // Handle the success response
        console.log(response);
        location.reload();
        // You can perform additional actions here
      },
      error: function(error) {
        // Handle the error response
        console.log(error);
        // You can perform additional error handling here
      }
    });
  }

  // Attach the click event handler to the checkboxes
  $('input[type="checkbox"]').on('click', function() {
    var id = $(this).data('task-id'); // Get the task ID from data attribute
    checkTask(id); // Call the checkTask function
  });
});