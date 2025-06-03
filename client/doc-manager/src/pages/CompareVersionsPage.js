import { useEffect, useState, useContext } from "react";
import { useParams } from "react-router-dom";
import ReactDiffViewer from "react-diff-viewer";
import api from "../api/client";
import { AuthContext } from "../context/AuthContext";
import Layout from "../components/Layout";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { 
  faExclamationTriangle, 
  faSpinner, 
  faCodeCompare,
  faFile,
  faInfoCircle
} from "@fortawesome/free-solid-svg-icons";

const CompareVersionsPage = () => {
  const { fileId } = useParams();
  const { token } = useContext(AuthContext);
  
  const [file, setFile] = useState(null);
  const [versions, setVersions] = useState([]);
  const [leftVersionId, setLeftVersionId] = useState("");
  const [rightVersionId, setRightVersionId] = useState("");
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch file details and versions
  useEffect(() => {
    const fetchFileDetails = async () => {
      try {
        const response = await api.get(`file_versions/${fileId}/`);
        const fileData = response.data;
        setFile(fileData);
        
        if (fileData.versions && fileData.versions.length > 0) {
          const sortedVersions = fileData.versions.sort((a, b) => b.version_number - a.version_number);
          setVersions(sortedVersions);
          
          // Set default selections: latest and previous version
          if (sortedVersions.length >= 2) {
            setLeftVersionId(sortedVersions[1].id.toString()); // Previous version
            setRightVersionId(sortedVersions[0].id.toString()); // Latest version
          } else if (sortedVersions.length === 1) {
            // Only one version, compare with itself
            setLeftVersionId(sortedVersions[0].id.toString());
            setRightVersionId(sortedVersions[0].id.toString());
          }
        }
      } catch (err) {
        console.error("Failed to fetch file details:", err);
        setError("Could not load file details.");
      }
    };

    if (fileId) {
      fetchFileDetails();
    }
  }, [fileId, token]);

  // Fetch comparison when version selections change
  useEffect(() => {
    if (leftVersionId && rightVersionId) {
      fetchComparison();
    }
  }, [leftVersionId, rightVersionId]);

  const fetchComparison = async () => {
    if (!leftVersionId || !rightVersionId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/compare/?left_id=${leftVersionId}&right_id=${rightVersionId}`);
      setComparison(response.data);
    } catch (err) {
      console.error("Failed to fetch comparison:", err);
      setError("Could not compare the selected versions. The files may not support text comparison.");
    } finally {
      setLoading(false);
    }
  };

  const getVersionLabel = (version) => {
    const isLatest = versions.length > 0 && version.version_number === Math.max(...versions.map(v => v.version_number));
    return `Version ${version.version_number}${isLatest ? ' (Latest)' : ''}`;
  };

  const isComparisonSupported = () => {
    if (!file) return false;
    
    const supportedTypes = [
      'text/plain',
      'text/markdown',
      'text/html',
      'application/xml',
      'text/xml',
      'application/json',
      'text/csv',
      'application/javascript',
      'text/javascript',
      'text/x-python',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/pdf'
    ];
    
    return supportedTypes.includes(file.mime_type);
  };

  if (!file) {
    return (
      <Layout>
        <div className="section">
          <div className="container">
            <div className="loading-state">
              <FontAwesomeIcon icon={faSpinner} spin size="2x" className="loading-icon" />
              <p className="loading-text">Loading file details...</p>
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
              <FontAwesomeIcon icon={faCodeCompare} className="mr-3" />
              Compare File Versions
            </h1>
          </div>

          {/* File Information Card */}
          <div className="file-info-card">
            <div className="file-info-header">
              <FontAwesomeIcon icon={faFile} className="file-info-icon" />
              <div className="file-info-details">
                <h2 className="file-info-name">{file.file_name}</h2>
                <div className="file-info-meta">
                  <span className="file-path">{file.virtual_path}</span>
                  <span className="file-type">Type: {file.mime_type}</span>
                </div>
              </div>
            </div>
          </div>

          {versions.length < 1 ? (
            <div className="alert alert-warning">
              <FontAwesomeIcon icon={faExclamationTriangle} className="mr-2" />
              No versions available for comparison.
            </div>
          ) : (
            <>
              {/* Version Selection */}
              <div className="version-selector-card">
                <h3 className="card-title">Select Versions to Compare</h3>
                <div className="version-selectors">
                  <div className="version-selector-group">
                    <label className="form-label">Left Version (Older)</label>
                    <div className="form-select">
                      <select 
                        value={leftVersionId} 
                        onChange={(e) => setLeftVersionId(e.target.value)}
                      >
                        {versions.map((version) => (
                          <option key={version.id} value={version.id}>
                            {getVersionLabel(version)}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  
                  <div className="version-selector-divider">
                    <FontAwesomeIcon icon={faCodeCompare} />
                  </div>
                  
                  <div className="version-selector-group">
                    <label className="form-label">Right Version (Newer)</label>
                    <div className="form-select">
                      <select 
                        value={rightVersionId} 
                        onChange={(e) => setRightVersionId(e.target.value)}
                      >
                        {versions.map((version) => (
                          <option key={version.id} value={version.id}>
                            {getVersionLabel(version)}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              {/* Error Messages */}
              {error && (
                <div className="alert alert-danger">
                  <FontAwesomeIcon icon={faExclamationTriangle} className="mr-2" />
                  {error}
                </div>
              )}

              {/* Unsupported File Type */}
              {!isComparisonSupported() ? (
                <div className="alert alert-info">
                  <FontAwesomeIcon icon={faInfoCircle} className="mr-2" />
                  <div>
                    <strong>File type not supported for comparison</strong>
                    <div className="text-small mt-1">
                      File type "{file.mime_type}" does not support text comparison. 
                      Only text-based files (documents, code, PDFs, etc.) can be compared.
                    </div>
                  </div>
                </div>
              ) : loading ? (
                <div className="loading-state">
                  <FontAwesomeIcon icon={faSpinner} spin size="2x" className="loading-icon" />
                  <p className="loading-text">Comparing versions...</p>
                </div>
              ) : comparison ? (
                <div className="diff-viewer-container">
                  <h3 className="diff-title">Version Comparison Results</h3>
                  <div className="diff-viewer-wrapper">
                    <ReactDiffViewer
                      oldValue={comparison.left_file.text}
                      newValue={comparison.right_file.text}
                      splitView={true}
                      leftTitle={`${comparison.left_file.name} (Left Version)`}
                      rightTitle={`${comparison.right_file.name} (Right Version)`}
                      showDiffOnly={false}
                      useDarkTheme={false}
                      hideLineNumbers={false}
                    />
                  </div>
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default CompareVersionsPage;