// Call loadModels() on page load
window.onload = function() {
    loadModels();
};

document.addEventListener('DOMContentLoaded', () => {
    loadModels(); // Load models on initial page load
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
        });
});
function loadModels() {
    const brandId = document.getElementById('brand_id').value;

    // Clear the current model dropdown
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
                console.log('Models:', models); // Check what models are being returned
                models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model[0]; // Use the first element for model_id
                    option.textContent = model[1]; // Use the second element for model name
                    modelSelect.appendChild(option);
                    console.log(`Added model: ${model[1]}`); // Log each model added
                });

                // Automatically select the first model if available
                if (models.length > 0) {
                    modelSelect.selectedIndex = 1; // Set to the first model option
                }
            })
            .catch(error => console.error('Error fetching models:', error));
    }
}




document.getElementById('customization-form').addEventListener('submit', function(event) {
    const modelSelect = document.getElementById('model_id');
    if (!modelSelect.value) {
        alert('Please select a model before submitting.');
        event.preventDefault();  // Prevent form submission
    }
});
