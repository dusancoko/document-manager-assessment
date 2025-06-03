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
  faUser,
  faEye,
  faEdit,
  faExclamationTriangle
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import Layout from "../components/Layout";

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

const SharedWithMePage = () => {
  const { token } = useContext(AuthContext);
  const history = useHistory();
  const [files, setFiles] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  // Track selected version for each file
  const [selectedVersions, setSelectedVersions] = useState({});

  useEffect(() => {
    const fetchSharedFiles = async () => {
      try {
        const response = await api.get("file_versions/shared-with-me/");
        setFiles(response.data);
        
        // Initialize selected versions to the latest version for each file
        const initialVersions = {};
        response.data.forEach(file => {
          // Set to the highest version number (latest version)
          const latestVersion = file.versions && file.versions.length > 0 
            ? Math.max(...file.versions.map(v => v.version_number))
            : file.version_number;
          initialVersions[file.id] = latestVersion;
        });
        setSelectedVersions(initialVersions);
      } catch (err) {
        console.error("Failed to fetch shared files", err);
        setError("Could not load shared files. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchSharedFiles();
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
    
    // If it's not the latest version, add revision parameter
    let url = `http://127.0.0.1:8001/api/download/${encodedPath}/?token=${token}`;
    if (selectedVersion && selectedVersion !== getLatestVersionNumber(fileId)) {
      // For older versions, use revision parameter (version numbers start from 1)
      url += `&revision=${selectedVersion}`;
    }
    
    window.open(url, "_blank");
  };

  const handleCompareVersions = (fileId) => {
    history.push(`/compare/${fileId}`);
  };

  const handleUploadNewVersion = (virtualPath, fileName) => {
    // Navigate to upload page with prefilled virtual path
    history.push({
      pathname: '/upload',
      state: { 
        prefillVirtualPath: virtualPath,
        prefillFileName: fileName 
      }
    });
  };

  const getLatestVersionNumber = (fileId) => {
    const file = files.find(f => f.id === fileId);
    if (file && file.versions && file.versions.length > 0) {
      return Math.max(...file.versions.map(v => v.version_number));
    }
    return file ? file.version_number : 1;
  };

  const getVersionsForFile = (file) => {
    // Use the versions array from the serializer if available
    if (file.versions && file.versions.length > 0) {
      return file.versions.sort((a, b) => b.version_number - a.version_number);
    } else {
      // Fallback to generating versions array
      return [...Array(file.version_number).keys()]
        .reverse()
        .map(v => ({
          id: file.id, // This is not accurate for older versions, but it's a fallback
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

  const hasPermission = (file, permission) => {
    return file.permissions && file.permissions.includes(permission);
  };

  const getPermissionBadge = (permissions) => {
    if (!permissions || permissions.length === 0) return null;
    
    return (
      <div className="permission-badges">
        {permissions.includes('view') && (
          <span className="permission-badge view">
            <FontAwesomeIcon icon={faEye} className="mr-1" />
            View
          </span>
        )}
        {permissions.includes('edit') && (
          <span className="permission-badge edit">
            <FontAwesomeIcon icon={faEdit} className="mr-1" />
            Edit
          </span>
        )}
      </div>
    );
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
              <p>Loading shared files...</p>
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
            <h1 className="page-title">
              <FontAwesomeIcon icon={faShareAlt} className="mr-3" />
              Shared with me
            </h1>
          </div>

          {error && (
            <div className="alert alert-danger">
              <FontAwesomeIcon icon={faExclamationTriangle} className="mr-2" />
              {error}
            </div>
          )}

          {files.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <FontAwesomeIcon icon={faShareAlt} />
              </div>
              <div className="empty-state-text">No files shared with you</div>
              <div className="empty-state-subtext">
                Files that others share with you will appear here
              </div>
            </div>
          ) : (
            files.map((file) => {
              const versions = getVersionsForFile(file);
              const selectedVersion = selectedVersions[file.id] || getLatestVersionNumber(file.id);
              const canEdit = hasPermission(file, 'edit');
              const canView = hasPermission(file, 'view');
              
              return (
                <div key={file.id} className="file-card shared-file-card">
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
                        <span>
                          <FontAwesomeIcon icon={faUser} className="mr-1" />
                          Shared by: {file.owner_email}
                        </span>
                        <span className="ml-3">
                          Size: {formatFileSize(file.file_size)}
                        </span>
                      </div>
                      <div className="file-path">{file.virtual_path}</div>
                      <div className="file-versions-and-permissions">
                        <span className="file-versions">
                          {versions.length} version{versions.length !== 1 ? 's' : ''} available
                        </span>
                        {getPermissionBadge(file.permissions)}
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
                        {canView && (
                          <button
                            className="btn btn-info btn-icon"
                            title={`Download version ${selectedVersion}`}
                            onClick={() => handleDownload(file.virtual_path, file.id)}
                          >
                            <FontAwesomeIcon icon={faDownload} />
                          </button>
                        )}
                        
                        {canEdit && (
                          <button
                            className="btn btn-warning btn-icon"
                            title="Upload new version"
                            onClick={() => handleUploadNewVersion(file.virtual_path, file.file_name)}
                          >
                            <FontAwesomeIcon icon={faUpload} />
                          </button>
                        )}
                        
                        {canView && (
                          <button
                            className="btn btn-secondary btn-icon"
                            title="Compare versions"
                            onClick={() => handleCompareVersions(file.id)}
                            disabled={versions.length < 2}
                          >
                            <FontAwesomeIcon icon={faCodeCompare} />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </Layout>
  );
};

export default SharedWithMePage;