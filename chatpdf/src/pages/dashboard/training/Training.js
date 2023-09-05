import Navbar from "components/navbar/Navbar";
import Sidebar from "components/sidebar/Sidebar";
import { Button, Form } from "react-bootstrap";
import "./training.scss";
import { useState } from "react";
import axios from "axios";
import { useRef, useEffect } from "react";
import { UploadFile, FiberManualRecord, WebAsset } from "@mui/icons-material";
import FileUploadMultiple from "components/uploading/UploadFile";
import { environment } from "environment";

export const Training = () => {
  const BASE_URL = environment.BASE_URL;
  const [oldFileName, setOldFileName] = useState("");
  const handleUpdate = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("oldFileName", oldFileName);
    const response = await axios.post(`${BASE_URL}/update_pdf/`, formData);
    console.log(response);
    if (response.status === 200) {
      alert("Deleted");
    }
  };
  return (
    <div className="training">
      <Sidebar />
      <div className="trainingContainer">
        <Navbar title="Training" />

        <div className="training_content">
          <h1>Train the model with new data</h1>
          <FileUploadMultiple />
          <h1>Delete already existing data</h1>
          <input
            type="text"
            placeholder="Input old file name here"
            value={oldFileName}
            onChange={(e) => setOldFileName(e.target.value)}
            style={{ width: "300px" }}
          />
          <br></br>
          <button style={{ width: "200px" }} onClick={handleUpdate}>
            Update
          </button>
        </div>
      </div>
    </div>
  );
};
