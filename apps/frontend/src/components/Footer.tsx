import { useState } from "react";
import { Resources } from "./Resources";

export function Footer() {
  const [showResources, setShowResources] = useState(false);
  const open = () => setShowResources(true);
  return (
    <>
      <footer className="footer">
        <div>
          <h4>Tools</h4>
          <ul>
            <li>DSC reader</li>
            <li>NMR (JCAMP / tsv / totxt)</li>
            <li>FTIR · Raman</li>
            <li>Format compare</li>
          </ul>
        </div>
        <div>
          <h4>Resources</h4>
          <ul>
            <li><a className="link" onClick={open}>Documentation</a></li>
            <li><a className="link" onClick={open}>Tutorials</a></li>
            <li><a className="link" onClick={open}>Examples</a></li>
            <li><a className="link" onClick={open}>Adding a reader</a></li>
          </ul>
        </div>
        <div>
          <h4>Contacts</h4>
          <ul>
            <li>
              <a href="https://github.com/yargerlab" target="_blank" rel="noreferrer">
                GitHub — yargerlab
              </a>
            </li>
            <li>Yarger Lab</li>
            <li><a className="link" onClick={open}>Feedback</a></li>
          </ul>
        </div>
      </footer>
      {showResources && <Resources onClose={() => setShowResources(false)} />}
    </>
  );
}
