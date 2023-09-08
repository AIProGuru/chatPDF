import { useState } from "react";
import axios from "axios";
import { environment } from "../../environment";

const FileUploadMultiple = () => {
  const BASE_URL = environment.BASE_URL;
  const [files, setFiles] = useState([]);

  const handleChange = (e) => {
    // Use Array.from to convert the FileList object to an array
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    const formData = new FormData();

    formData.append("length", files.length);

    files.forEach((file, index) => {
      formData.append(`file-${index}`, file);
    });

    try {
      const response = await axios.post(
        `${BASE_URL}/upload_documents/`,
        formData
      );
      console.log(response.status);
      if (response.status === 200) {
        alert("Training completed");
      }
      console.log(response);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <div className="upload_container">
        <form onSubmit={handleUpload}>
          <label className="custom-file-upload">
            Choose Files
            <i className="fa fa-upload"></i>
            {/* Set the 'multiple' attribute to allow multiple file selection */}
            <input type="file" multiple onChange={handleChange} />
          </label>
          <button type="submit">Train</button>
        </form>
      </div>
    </div>
  );
};

export default FileUploadMultiple;
