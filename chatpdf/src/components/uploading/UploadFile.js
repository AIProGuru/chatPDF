import { useState } from "react";
import axios from "axios";
import { environment } from "../../environment";

const FileUploadMultiple = () => {
  const BASE_URL = environment.BASE_URL;
  const [files, setFiles] = useState([]);
  const [isTraining, setIsTraining] = useState(false);

  const handleChange = (e) => {
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
      setIsTraining(true); // Set loading indicator to true
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
    } finally {
      setIsTraining(false); // Set loading indicator back to false
    }
  };

  return (
    <div>
      <div className="upload_container">
        <form onSubmit={handleUpload}>
          <label className="custom-file-upload">
            Choose Files
            <i className="fa fa-upload"></i>
            <input type="file" multiple onChange={handleChange} />
          </label>
          <button type="submit" disabled={isTraining}>
            {isTraining ? "Training in progress..." : "Train"}
          </button>
        </form>
      </div>
      {isTraining && <p>Training in progress. Please wait ...</p>}
    </div>
  );
};
export default FileUploadMultiple;
