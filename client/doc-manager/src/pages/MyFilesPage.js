import { useEffect, useState, useContext } from "react";
import { useHistory } from "react-router-dom";
import api from "../api/client";
import { AuthContext } from "../context/AuthContext";
import {
  faDownload,
  faUpload,
  faCodeCompare,
  faFileAlt,
  faFilePdf,
  faFileImage,
  faFileWord,
  faFileExcel,
  faFileArchive,
  faFolder,
  faShareAlt,
  faCheckCircle
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Layout from "../components/Layout";
import FileShareModal from "../components/FileShareModal";

const mimeToIcon = (mimeType) => {
  if (mimeType.includes("pdf")) return faFilePdf;
  if (mimeType.includes("image")) return faFileImage;
  if (mimeType.includes("word")) return faFileWord;
  if (mimeType.includes("excel") || mimeType.includes("spreadsheet"))
    return faFileExcel;
  if (mimeType.includes("zip") || mimeType.includes("compressed"))
    return faFileArchive;
  return faFileAlt;
};

const MyFilesPage = () => {
  const { token } = useContext(AuthContext);
  const history = useHistory();
  const [files, setFiles] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedVersions, setSelectedVersions] = useState({});
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [fileToShare, setFileToShare] = useState(null);
  const [shareMessage, setShareMessage] = useState("");

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const response = await api.get("file_versions/");
        setFiles(response.data);
        
        // Initialize selected versions to the latest version for each file
        const initialVersions = {};
        response.data.forEach(file => {
          const latestVersion = file.versions && file.versions.length > 0 
            ? Math.max(...file.versions.map(v => v.version_number))
            : file.version_number;
          initialVersions[file.id] = latestVersion;
        });
        setSelectedVersions(initialVersions);
      } catch (err) {
        console.error("Failed to fetch files", err);
        setError("Could not load files. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchFiles();
  }, [token]);

  const handleVersionChange = (fileId, versionNumber) => {
    setSelectedVersions(prev => ({
      ...prev,
      [fileId]: parseInt(versionNumber)
    }));
  };

  const handleDownload = (virtualPath, fileId) => {
    const selectedVersion = selectedVersions[fileId];
    const encodedPath = encodeURIComponent(virtualPath);
    
    let url = `http://127.0.0.1:8001/api/download/${encodedPath}/?token=${token}`;
    if (selectedVersion && selectedVersion !== getLatestVersionNumber(fileId)) {
      url += `&revision=${selectedVersion}`;
    }
    
    window.open(url, "_blank");
  };

  const handleCompareVersions = (fileId) => {
    history.push(`/compare/${fileId}`);
  };

  const handleUploadNewVersion = (virtualPath, fileName) => {
    history.push({
      pathname: '/upload',
      state: { 
        prefillVirtualPath: virtualPath,
        prefillFileName: fileName 
      }
    });
  };

  const handleShareFile = (file) => {
    setFileToShare(file);
    setShareModalOpen(true);
  };

  const handleShareSuccess = (message) => {
    setShareMessage(message);
    setTimeout(() => setShareMessage(""), 5000); // Clear message after 5 seconds
  };

  const getLatestVersionNumber = (fileId) => {
    const file = files.find(f => f.id === fileId);
    if (file && file.versions && file.versions.length > 0) {
      return Math.max(...file.versions.map(v => v.version_number));
    }
    return file ? file.version_number : 1;
  };

  const getVersionsForFile = (file) => {
    if (file.versions && file.versions.length > 0) {
      return file.versions.sort((a, b) => b.version_number - a.version_number);
    } else {
      return [...Array(file.version_number).keys()]
        .reverse()
        .map(v => ({
          id: file.id,
          version_number: v + 1,
          virtual_path: file.virtual_path
        }));
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <Layout>
        <div className="section">
          <div className="container">
            <div className="text-center">
              <div className="empty-state-icon">
                <FontAwesomeIcon icon={faFolder} />
              </div>
              <p>Loading your files...</p>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="section">
        <div className="container">
          <div className="page-header">
            <h1 className="page-title">My Files</h1>
          </div>

          {error && (
            <div className="alert alert-danger">
              {error}
            </div>
          )}

          {shareMessage && (
            <div className="alert alert-success">
              <FontAwesomeIcon icon={faCheckCircle} className="mr-2" />
              {shareMessage}
            </div>
          )}

          {files.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <FontAwesomeIcon icon={faFolder} />
              </div>
              <div className="empty-state-text">No files uploaded yet</div>
              <div className="empty-state-subtext">
                Start by uploading your first document
              </div>
              <div className="mt-4">
                <button 
                  className="btn btn-primary"
                  onClick={() => history.push('/upload')}
                >
                  <FontAwesomeIcon icon={faUpload} className="mr-2" />
                  Upload File
                </button>
              </div>
            </div>
          ) : (
            files.map((file) => {
              const versions = getVersionsForFile(file);
              const selectedVersion = selectedVersions[file.id] || getLatestVersionNumber(file.id);
              
              return (
                <div key={file.id} className="file-card">
                  <div className="file-card-content">
                    <div className="file-icon">
                      <FontAwesomeIcon
                        icon={mimeToIcon(file.mime_type)}
                        size="lg"
                      />
                    </div>
                    
                    <div className="file-details">
                      <div className="file-name">{file.file_name}</div>
                      <div className="file-meta">
                        Size: {formatFileSize(file.file_size)} | 
                        Checksum: {file.checksum.substring(0, 12)}...
                      </div>
                      <div className="file-path">{file.virtual_path}</div>
                      <div className="file-versions">
                        {versions.length} version{versions.length !== 1 ? 's' : ''} available
                      </div>
                    </div>

                    <div className="file-controls">
                      <div className="version-selector">
                        <div className="form-select select-small">
                          <select 
                            value={selectedVersion}
                            onChange={(e) => handleVersionChange(file.id, e.target.value)}
                          >
                            {versions.map((version) => (
                              <option key={version.version_number} value={version.version_number}>
                                Version {version.version_number}
                                {version.version_number === getLatestVersionNumber(file.id) ? ' (Latest)' : ''}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div className="action-buttons">
                        <button
                          className="btn btn-info btn-icon"
                          title={`Download version ${selectedVersion}`}
                          onClick={() => handleDownload(file.virtual_path, file.id)}
                        >
                          <FontAwesomeIcon icon={faDownload} />
                        </button>
                        <button
                          className="btn btn-warning btn-icon"
                          title="Upload new version"
                          onClick={() => handleUploadNewVersion(file.virtual_path, file.file_name)}
                        >
                          <FontAwesomeIcon icon={faUpload} />
                        </button>
                        <button
                          className="btn btn-success btn-icon"
                          title="Share file"
                          onClick={() => handleShareFile(file)}
                        >
                          <FontAwesomeIcon icon={faShareAlt} />
                        </button>
                        <button
                          className="btn btn-secondary btn-icon"
                          title="Compare versions"
                          onClick={() => handleCompareVersions(file.id)}
                          disabled={versions.length < 2}
                        >
                          <FontAwesomeIcon icon={faCodeCompare} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}

          {/* File Share Modal */}
          {fileToShare && (
            <FileShareModal
              file={fileToShare}
              isOpen={shareModalOpen}
              onClose={() => {
                setShareModalOpen(false);
                setFileToShare(null);
              }}
              onSuccess={handleShareSuccess}
            />
          )}
        </div>
      </div>
    </Layout>
  );
};

export default MyFilesPage;