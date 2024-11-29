// Call loadModels() on page load
window.onload = function() {
    loadModels();
};

document.addEventListener('DOMContentLoaded', () => {
    loadModels(); // Load models on initial page load
    styleDropdowns(); // Apply styles to dropdowns
});

document.addEventListener('DOMContentLoaded', function() {
    const brandSelect = document.getElementById('brand');
    
    if (brandSelect) {
        brandSelect.addEventListener('change', function() {
            const brandId = this.value;
            if (!brandId) return;
            
            fetch(`/get_models/${brandId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    const modelSelect = document.getElementById('model');
                    
                    // Clear existing options
                    modelSelect.innerHTML = '<option value="" disabled selected>Select a model</option>';
                    
                    // Add new options
                    data.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model.model_id;  // Set the correct model_id
                        option.textContent = model.name;  // Set the model name
                        modelSelect.appendChild(option);
                    });
                    
                    // Re-apply any custom styling
                    if (typeof styleDropdowns === 'function') {
                        styleDropdowns();
                    }
                })
                .catch(error => {
                    console.error('Error fetching models:', error);
                    const modelSelect = document.getElementById('model');
                    modelSelect.innerHTML = '<option value="" disabled selected>Error loading models</option>';
                });
        });
    }
    
    // Add listener for model selection change
    const modelSelect = document.getElementById('model');
    if (modelSelect) {
        modelSelect.addEventListener('change', function() {
            const modelId = this.value;  // Get the value of the selected option (model_id)
            console.log('Selected Model ID:', modelId);  // Debugging
            if (modelId) {
                document.getElementById('model_id').value = modelId;  // Set model_id in hidden field
            }
        });
    }

    if (typeof styleDropdowns === 'function') {
        styleDropdowns();
    }
});




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