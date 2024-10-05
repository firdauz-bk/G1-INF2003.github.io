
document.addEventListener('DOMContentLoaded', function() {
    var ctx = document.getElementById('dataChart').getContext('2d');
    var chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['January', 'February', 'March', 'April', 'May', 'June', 'July'],
            datasets: [{
                label: 'Users',
                data: [65, 59, 80, 81, 56, 55, 40],
                fill: false,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }, {
                label: 'Vehicle Types',
                data: [28, 48, 40, 19, 86, 27, 90],
                fill: false,
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }, {
                label: 'Brands',
                data: [17, 28, 39, 20, 46, 27, 60],
                fill: false,
                borderColor: 'rgb(255, 205, 86)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
});

