import { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faShareAlt, faTimes, faUserPlus, faEye, faEdit } from "@fortawesome/free-solid-svg-icons";
import api from "../api/client";

const FileShareModal = ({ file, isOpen, onClose, onSuccess }) => {
  const [userEmail, setUserEmail] = useState("");
  const [canEdit, setCanEdit] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userEmail.trim()) {
      setError("Email is required");
      return;
    }

    setSharing(true);
    setError(null);

    try {
      const response = await api.post("/share/", {
        file_id: file.id,
        user_email: userEmail.trim(),
        can_edit: canEdit
      });

      onSuccess(response.data.message);
      onClose();
      setUserEmail("");
      setCanEdit(false);
    } catch (err) {
      if (err.response && err.response.data) {
        setError(err.response.data.detail || "Failed to share file");
      } else {
        setError("An error occurred while sharing the file");
      }
    } finally {
      setSharing(false);
    }
  };

  const handleClose = () => {
    setUserEmail("");
    setCanEdit(false);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">
            <FontAwesomeIcon icon={faShareAlt} className="mr-2" />
            Share File
          </h3>
          <button className="modal-close" onClick={handleClose}>
            <FontAwesomeIcon icon={faTimes} />
          </button>
        </div>

        <div className="modal-body">
          <div className="share-file-info">
            <p className="text-grey mb-4">
              Share "<strong>{file.file_name}</strong>" with another user
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label" htmlFor="userEmail">
                <FontAwesomeIcon icon={faUserPlus} className="mr-2" />
                User Email
              </label>
              <input
                id="userEmail"
                className="form-input"
                type="email"
                placeholder="Enter user's email address"
                value={userEmail}
                onChange={(e) => setUserEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <div className="permission-options">
                <h4 className="permission-title">Permissions</h4>
                
                <div className="permission-option">
                  <input
                    type="radio"
                    id="viewOnly"
                    name="permissions"
                    checked={!canEdit}
                    onChange={() => setCanEdit(false)}
                  />
                  <label htmlFor="viewOnly" className="permission-label">
                    <FontAwesomeIcon icon={faEye} className="mr-2" />
                    <div>
                      <div className="permission-name">View only</div>
                      <div className="permission-description">
                        User can view and download the file
                      </div>
                    </div>
                  </label>
                </div>

                <div className="permission-option">
                  <input
                    type="radio"
                    id="canEdit"
                    name="permissions"
                    checked={canEdit}
                    onChange={() => setCanEdit(true)}
                  />
                  <label htmlFor="canEdit" className="permission-label">
                    <FontAwesomeIcon icon={faEdit} className="mr-2" />
                    <div>
                      <div className="permission-name">Can edit</div>
                      <div className="permission-description">
                        User can view, download, and upload new versions
                      </div>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            {error && (
              <div className="alert alert-danger">
                {error}
              </div>
            )}

            <div className="modal-actions">
              <button
                type="button"
                className="btn btn-light mr-3"
                onClick={handleClose}
                disabled={sharing}
              >
                Cancel
              </button>
              <button
                type="submit"
                className={`btn btn-primary ${sharing ? "btn-loading" : ""}`}
                disabled={sharing}
              >
                {sharing ? "Sharing..." : "Share File"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default FileShareModal;