$(document).ready(function() {
    $('.circlechart').each(function() {
        var percentage = $(this).data('percentage');
        $(this).circleProgress({
            value: percentage / 100,
            size: 200,
            thickness: 10,
            fill: {
                color: '#007ced'
            },
            emptyFill: '#333',
            animation: {
                duration: 1500
            }
        }).on('circle-animation-progress', function(event, progress, stepValue) {
            $(this).find('strong').text(Math.round(stepValue * 100) + '%');
        });
    });
});


document.querySelector('.form-box').addEventListener('submit', async function(e) {
  e.preventDefault(); // Prevent default form submission/reload

  // Collect form data
  const firstName = document.getElementById('firstName').value.trim();
  const lastName = document.getElementById('lastName').value.trim();
  const email = document.getElementById('email').value.trim();
  const phoneNumber = document.getElementById('phoneNumber').value.trim();
  const message = document.getElementById('message').value.trim();

  try {
    const response = await fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ firstName, lastName, email, phoneNumber, message }),
    });

    const result = await response.json();

    if (response.ok) {
      alert('Thank you for contacting me! I will get back to you soon.');
      this.reset(); // Clear form
    } else {
      alert('Oops! Something went wrong: ' + (result.error || 'Unknown error'));
    }
  } catch (error) {
    alert('Network error: ' + error.message);
  }
});
