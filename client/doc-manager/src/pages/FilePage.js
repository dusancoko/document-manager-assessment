import { useParams } from "react-router-dom";

function FilePage() {
  const { fileId } = useParams();

  return (
    <section className="section">
      <div className="container">
        <h1 className="title">You are visiting File Page for ID: {fileId}</h1>
      </div>
    </section>
  );
}

export default FilePage;
