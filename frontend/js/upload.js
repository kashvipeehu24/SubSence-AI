document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('fileInput');
  const selectedFile = document.getElementById('selectedFile');
  const dropZone = document.querySelector('.drop-zone');

  if (!fileInput || !selectedFile || !dropZone) return;

  fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    selectedFile.textContent = file ? file.name : 'No file selected yet.';
  });

  dropZone.addEventListener('dragover', (event) => {
    event.preventDefault();
    dropZone.style.borderColor = '#63e4c0';
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.style.borderColor = '#63e4c0';
  });

  dropZone.addEventListener('drop', (event) => {
    event.preventDefault();
    dropZone.style.borderColor = '#63e4c0';

    const file = event.dataTransfer.files[0];
    if (file) {
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      fileInput.files = dataTransfer.files;
      selectedFile.textContent = file.name;
    }
  });
});

  
  