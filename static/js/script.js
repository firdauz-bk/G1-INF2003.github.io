// Call loadModels() on page load
window.onload = function() {
    loadModels();
};

document.addEventListener('DOMContentLoaded', () => {
    loadModels(); // Load models on initial page load
    styleDropdowns(); // Apply styles to dropdowns
});

document.getElementById('brand_id').addEventListener('change', function() {
    const brandId = this.value;
    fetch(`/get_models/${brandId}`)
        .then(response => response.json())
        .then(data => {
            const modelSelect = document.getElementById('model_id');
            modelSelect.innerHTML = '<option value="" disabled selected>Select a model</option>';
            data.forEach(model => {
                const option = document.createElement('option');
                option.value = model[0];
                option.textContent = model[1];
                modelSelect.appendChild(option);
            });
            styleDropdowns(); // Re-apply styles after populating
        });
});

function loadModels() {
    const brandId = document.getElementById('brand_id').value;
    const modelSelect = document.getElementById('model_id');
    modelSelect.innerHTML = '<option value="" disabled selected>Select a model</option>';

    if (brandId) {
        fetch(`/get_models/${brandId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(models => {
                console.log('Models:', models);
                models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model[0];
                    option.textContent = model[1];
                    modelSelect.appendChild(option);
                    console.log(`Added model: ${model[1]}`);
                });

                if (models.length > 0) {
                    modelSelect.selectedIndex = 1;
                }
                styleDropdowns(); // Apply styles after populating
            })
            .catch(error => console.error('Error fetching models:', error));
    }
}

document.getElementById('customization-form').addEventListener('submit', function(event) {
    const modelSelect = document.getElementById('model_id');
    if (!modelSelect.value) {
        alert('Please select a model before submitting.');
        event.preventDefault();
    }
});

// Function to apply styles to dropdowns
function styleDropdowns() {
    const dropdowns = document.querySelectorAll('select');
    dropdowns.forEach(dropdown => {
        dropdown.style.backgroundColor = '#3d3d3d';
        dropdown.style.color = '#ffffff';
        dropdown.style.border = '1px solid #4d4d4d';
        dropdown.style.borderRadius = '4px';
        dropdown.style.padding = '5px';
    });
}