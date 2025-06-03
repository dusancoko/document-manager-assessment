import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import Layout from "../components/Layout";
import api from "../api/client";
import { useForm } from "react-hook-form";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faUpload, faFile, faCheckCircle } from "@fortawesome/free-solid-svg-icons";

const UploadPage = () => {
  const location = useLocation();
  const { register, handleSubmit, reset, setValue, watch } = useForm();
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState(null);
  const [message, setMessage] = useState("");

  // Watch the file input for changes
  const watchedFile = watch("file");

  // Auto-populate display name when file is selected
  useEffect(() => {
    if (watchedFile && watchedFile[0]) {
      const fileName = watchedFile[0].name;
      setValue("name", fileName);
    }
  }, [watchedFile, setValue]);

  // Check if we have prefilled data from navigation state
  useEffect(() => {
    if (location.state) {
      if (location.state.prefillVirtualPath) {
        setValue("virtual_path", location.state.prefillVirtualPath);
      }
      if (location.state.prefillFileName) {
        setValue("name", location.state.prefillFileName);
      }
    }
  }, [location.state, setValue]);

  const onSubmit = async (data) => {
    if (!data.file[0] || !data.virtual_path) {
      setUploadError("File and virtual path are required.");
      return;
    }

    const formData = new FormData();
    formData.append("file", data.file[0]);
    formData.append("virtual_path", data.virtual_path);
    formData.append("name", data.name || data.file[0].name);

    try {
      setUploading(true);
      setUploadProgress(0);
      setMessage("");
      setUploadError(null);

      const response = await api.post("/upload/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percent);
        },
      });

      setMessage(`Upload successful! Version ${response.data.version} created.`);
      reset();
    } catch (error) {
      if (error.response && error.response.data) {
        setUploadError(error.response.data.detail || "Upload failed. Please try again.");
      } else if (error.message) {
        setUploadError(error.message);
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <Layout>
      <div className="section">
        <div className="container">
          <div className="page-header">
            <h1 className="page-title">
              <FontAwesomeIcon icon={faUpload} className="mr-3" />
              Upload File
            </h1>
          </div>

          <div className="upload-container">
            {location.state && location.state.prefillVirtualPath && (
              <div className="alert alert-info mb-4">
                <FontAwesomeIcon icon={faFile} className="mr-2" />
                <strong>Uploading new version for:</strong> {location.state.prefillVirtualPath}
                <div className="text-small mt-1">
                  This will create a new version of the existing file.
                </div>
              </div>
            )}

            <div className="upload-card">
              <form onSubmit={handleSubmit(onSubmit)}>
                <div className="form-group">
                  <label className="form-label" htmlFor="file">
                    Select File *
                  </label>
                  <div className="file-input-wrapper">
                    <input
                      id="file"
                      className="file-input"
                      type="file"
                      {...register("file", { required: true })}
                    />
                    <div className="file-input-placeholder">
                      <FontAwesomeIcon icon={faFile} className="mr-2" />
                      {watchedFile && watchedFile[0] ? watchedFile[0].name : "Choose a file to upload"}
                    </div>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="name">
                    Display Name
                  </label>
                  <input 
                    id="name"
                    className="form-input" 
                    type="text" 
                    placeholder="File display name"
                    {...register("name")} 
                  />
                  <div className="form-help">
                    Auto-populated from filename. You can customize it if needed.
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="virtual_path">
                    Virtual Path *
                  </label>
                  <input
                    id="virtual_path"
                    className="form-input"
                    type="text"
                    placeholder="/documents/example.txt"
                    {...register("virtual_path", { required: true })}
                  />
                  <div className="form-help">
                    Use the same path as an existing file to create a new version, or a new path for a new file.
                  </div>
                </div>

                {uploading && (
                  <div className="progress-container">
                    <label className="form-label">Upload Progress</label>
                    <div className="progress-wrapper">
                      <div className="progress">
                        <div 
                          className="progress-bar" 
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                      <span className="progress-text">{uploadProgress}%</span>
                    </div>
                  </div>
                )}

                <div className="form-actions">
                  <button
                    className={`btn btn-primary btn-large ${uploading ? "btn-loading" : ""}`}
                    type="submit"
                    disabled={uploading}
                  >
                    <FontAwesomeIcon icon={faUpload} className="mr-2" />
                    {uploading ? "Uploading..." : "Upload File"}
                  </button>
                </div>
              </form>

              {message && (
                <div className="alert alert-success mt-4">
                  <FontAwesomeIcon icon={faCheckCircle} className="mr-2" />
                  {message}
                </div>
              )}
              
              {uploadError && (
                <div className="alert alert-danger mt-4">
                  {uploadError}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default UploadPage;