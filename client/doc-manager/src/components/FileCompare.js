import { useParams } from "react-router-dom";

function FileCompare() {
  const { id1, id2 } = useParams();

  return (
    <section className="section">
      <div className="container">
        <h1 className="title">
          Comparing file version {id1} with {id2}
        </h1>
      </div>
    </section>
  );
}

export default FileCompare;
