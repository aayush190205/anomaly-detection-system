import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  ShieldAlert,
  ShieldCheck,
  Send,
  Bot,
  User,
  Activity,
  LayoutDashboard,
  Settings,
  FileText,
  Database,
  Server,
  Cpu,
  AlertTriangle,
  Clock,
  CheckCircle,
  Loader2,
  RefreshCw,
  Save,
  Sliders,
  BarChart3
} from "lucide-react";

const API = "http://localhost:5000";

function App() {
  const [currentView, setCurrentView] = useState("live");
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      type: "info",
      text: "Behaviour IDS is online.\n\nPaste a JSON event to begin building behavioural history.\n\nPredictions begin after the backend has collected enough events for the same entity."
    }
  ]);
  const [inputLog, setInputLog] = useState("");
  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [backendStatus, setBackendStatus] = useState(null);
  const [modelVersion, setModelVersion] = useState("-");
  const [sequenceLength, setSequenceLength] = useState(10);
  const [requestsProcessed, setRequestsProcessed] = useState(0);
  const [trackedEntities, setTrackedEntities] = useState(0);
  const [history, setHistory] = useState([]);
  const [threshold, setThreshold] = useState(85);
  const [explainer, setExplainer] = useState("SHAP");
  const [dashboard, setDashboard] = useState({
    normal: 0,
    anomaly: 0,
    pending: 0,
    averageConfidence: 0
  });

  const fetchBackendStatus = async () => {
    try {
      const health = await axios.get(`${API}/health`);
      const status = await axios.get(`${API}/api/status`);
      setBackendOnline(true);
      setBackendStatus(health.data);
      setModelVersion(health.data.model_version);
      setSequenceLength(health.data.sequence_length);
      setTrackedEntities(health.data.tracked_entities);
      setRequestsProcessed(status.data.requests_processed);
    }
    catch {
      setBackendOnline(false);
    }
  };

  useEffect(() => {
    fetchBackendStatus();
    const timer = setInterval(fetchBackendStatus, 5000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    let normal = 0;
    let anomaly = 0;
    let pending = 0;
    let confidence = 0;
    history.forEach(item => {
      if (item.classification_type === "Normal")
        normal++;
      else if (item.classification_type === "Anomaly")
        anomaly++;
      else
        pending++;
      confidence += item.confidence || 0;
    });
    setDashboard({
      normal,
      anomaly,
      pending,
      averageConfidence: history.length === 0 ? 0 : (confidence / history.length).toFixed(1)
    });
  }, [history]);

  const resetBackend = async () => {
    try {
      await axios.post(`${API}/api/reset`);
      setMessages([
        {
          sender: "bot",
          type: "info",
          text: "Runtime history cleared successfully."
        }
      ]);
      setHistory([]);
      fetchBackendStatus();
    }
    catch {
      alert("Unable to reset backend.");
    }
  };

  const handleAnalyze = async () => {
    if (!inputLog.trim() || loading) return;
    setLoading(true);
    setMessages(prev => [
      ...prev,
      {
        sender: "user",
        text: inputLog
      }
    ]);
    try {
      const match = inputLog.match(/\{[\s\S]*\}/);
      if (!match)
        throw new SyntaxError("No JSON object found.");
      const payload = JSON.parse(match[0]);
      const { data } = await axios.post(`${API}/api/analyze`, payload);
      if (data.status === "waiting") {
        setMessages(prev => [
          ...prev,
          {
            sender: "bot",
            type: "waiting",
            waiting: true,
            prediction: data.prediction,
            confidence: 0,
            classification_type: data.classification_type,
            eventsCollected: data.events_collected,
            eventsRequired: data.events_required,
            message: data.message
          }
        ]);
        setHistory(prev => [
          {
            timestamp: new Date().toLocaleTimeString(),
            rawLog: match[0],
            prediction: "Collecting History",
            classification_type: "Pending",
            confidence: 0
          },
          ...prev
        ]);
        setInputLog("");
        fetchBackendStatus();
        setLoading(false);
        return;
      }
      if (data.status === "success") {
        const botMessage = {
          sender: "bot",
          type: "prediction",
          prediction: data.prediction,
          confidence: data.confidence,
          classification_type: data.classification_type,
          entity_id: data.entity_id,
          events_used: data.events_used,
          history_size: data.history_size,
          top_features: data.top_features || [],
          class_probabilities: data.class_probabilities || {},
          timestamp: data.timestamp,
          model_version: data.model_version,
          isAnomaly: data.classification_type === "Anomaly"
        };
        setMessages(prev => [
          ...prev,
          botMessage
        ]);
        setHistory(prev => [
          {
            rawLog: match[0],
            ...botMessage
          },
          ...prev
        ]);
        fetchBackendStatus();
      }
      else {
        setMessages(prev => [
          ...prev,
          {
            sender: "bot",
            type: "error",
            text: data.message || "Prediction failed."
          }
        ]);
      }
    }
    catch (err) {
      let message = "Unable to reach backend.";
      if (err instanceof SyntaxError) {
        message = err.message;
      }
      else if (err.response) {
        message = err.response.data.message || "Server error.";
      }
      else if (err.request) {
        message = "Cannot connect to Flask backend.";
      }
      setMessages(prev => [
        ...prev,
        {
          sender: "bot",
          type: "error",
          text: message
        }
      ]);
    }
    setInputLog("");
    setLoading(false);
  };

  const pct = value => {
    if (value === undefined || value === null)
      return "0.00";
    return Number(value).toFixed(2);
  };

  const probabilityColour = value => {
    if (value >= 80)
      return "#10b981";
    if (value >= 50)
      return "#f59e0b";
    return "#ef4444";
  };

  const predictionColour = type =>
    type === "Anomaly" ? "#ef4444" : "#10b981";

  const renderLiveAnalysis = () => (
    <>
      <main
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "30px",
          display: "flex",
          flexDirection: "column",
          gap: "22px"
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              display: "flex",
              gap: "16px",
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              maxWidth: "88%"
            }}
          >
            {msg.sender === "bot" && (
              <div
                style={{
                  background: "#fff",
                  border: "1px solid #e2e8f0",
                  borderRadius: 10,
                  padding: 10,
                  height: "fit-content"
                }}
              >
                <Bot
                  size={22}
                  color="#2563eb"
                />
              </div>
            )}
            <div
              style={{
                background: msg.sender === "user" ? "#0f172a" : "#fff",
                color: msg.sender === "user" ? "#fff" : "#111827",
                border: msg.sender === "bot" ? "1px solid #e2e8f0" : "none",
                borderRadius: 14,
                padding: 20,
                width: "100%"
              }}
            >
              {msg.text && (
                <pre
                  style={{
                    margin: 0,
                    whiteSpace: "pre-wrap",
                    fontFamily: msg.sender === "user" ? "monospace" : "inherit",
                    fontSize: 14
                  }}
                >
                  {msg.text}
                </pre>
              )}
              {msg.waiting && (
                <div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      marginBottom: 15
                    }}
                  >
                    <Clock
                      color="#f59e0b"
                      size={24}
                    />
                    <h3
                      style={{
                        margin: 0
                      }}
                    >
                      Building Behaviour History
                    </h3>
                  </div>
                  <div
                    style={{
                      marginBottom: 15,
                      color: "#475569"
                    }}
                  >
                    {msg.message}
                  </div>
                  <div
                    style={{
                      width: "100%",
                      background: "#e5e7eb",
                      borderRadius: 10,
                      overflow: "hidden",
                      height: 14
                    }}
                  >
                    <div
                      style={{
                        width: `${(msg.eventsCollected / msg.eventsRequired) * 100}%`,
                        background: "#2563eb",
                        height: "100%"
                      }}
                    />
                  </div>
                  <div
                    style={{
                      marginTop: 10,
                      fontSize: 13,
                      color: "#64748b"
                    }}
                  >
                    {msg.eventsCollected} / {msg.eventsRequired} events collected
                  </div>
                </div>
              )}
              {msg.type === "prediction" && (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 20
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      borderBottom: "1px solid #e5e7eb",
                      paddingBottom: 14
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        gap: 10,
                        alignItems: "center"
                      }}
                    >
                      {msg.isAnomaly ? (
                        <ShieldAlert
                          color="#ef4444"
                          size={26}
                        />
                      ) : (
                        <ShieldCheck
                          color="#10b981"
                          size={26}
                        />
                      )}
                      <div>
                        <h3
                          style={{
                            margin: 0,
                            color: predictionColour(msg.classification_type)
                          }}
                        >
                          {msg.prediction}
                        </h3>
                        <div
                          style={{
                            fontSize: 13,
                            color: "#64748b"
                          }}
                        >
                          {msg.classification_type}
                        </div>
                      </div>
                    </div>
                    <div
                      style={{
                        background: "#f8fafc",
                        padding: "8px 14px",
                        borderRadius: 8,
                        border: "1px solid #e5e7eb",
                        fontWeight: 600
                      }}
                    >
                      {pct(msg.confidence)}%
                    </div>
                  </div>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(4,1fr)",
                      gap: 16
                    }}
                  >
                    <InfoCard
                      title="Entity"
                      value={msg.entity_id}
                    />
                    <InfoCard
                      title="Sequence"
                      value={msg.events_used}
                    />
                    <InfoCard
                      title="History"
                      value={msg.history_size}
                    />
                    <InfoCard
                      title="Version"
                      value={msg.model_version}
                    />
                  </div>
                  <div>
                    <h4
                      style={{
                        marginBottom: 10
                      }}
                    >
                      Top Features
                    </h4>
                    <div
                      style={{
                        display: "grid",
                        gap: 10
                      }}
                    >
                      {msg.top_features.map((feature, i) => (
                        <div
                          key={i}
                          style={{
                            border: "1px solid #e5e7eb",
                            borderRadius: 10,
                            padding: 12,
                            display: "flex",
                            justifyContent: "space-between"
                          }}
                        >
                          <div>
                            <strong>
                              {feature.feature}
                            </strong>
                            <div
                              style={{
                                fontSize: 13,
                                color: "#64748b"
                              }}
                            >
                              {feature.direction}
                            </div>
                          </div>
                          <div
                            style={{
                              fontWeight: 600
                            }}
                          >
                            {feature.impact}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4
                      style={{
                        marginBottom: 12
                      }}
                    >
                      Class Probabilities
                    </h4>
                    {Object.entries(msg.class_probabilities).map(([label, value]) => (
                      <div
                        key={label}
                        style={{
                          marginBottom: 14
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            marginBottom: 4
                          }}
                        >
                          <span>
                            {label}
                          </span>
                          <span>
                            {pct(value)}%
                          </span>
                        </div>
                        <div
                          style={{
                            height: 10,
                            background: "#e5e7eb",
                            borderRadius: 10,
                            overflow: "hidden"
                          }}
                        >
                          <div
                            style={{
                              width: `${value}%`,
                              height: "100%",
                              background: probabilityColour(value)
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {msg.sender === "user" && (
              <div
                style={{
                  background: "#0f172a",
                  borderRadius: 10,
                  padding: 10,
                  height: "fit-content"
                }}
              >
                <User
                  color="white"
                  size={22}
                />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginLeft: 55,
              color: "#64748b"
            }}
          >
            <Loader2
              size={18}
              className="animate-spin"
            />
            Analysing behavioural sequence...
          </div>
        )}
      </main>
      <div
        style={{
          background: "#fff",
          borderTop: "1px solid #e5e7eb",
          padding: 24
        }}
      >
        <div
          style={{
            display: "flex",
            gap: 18
          }}
        >
          <textarea
            value={inputLog}
            onChange={(e) => setInputLog(e.target.value)}
            placeholder="Paste a JSON event..."
            style={{
              flex: 1,
              height: 120,
              resize: "none",
              borderRadius: 10,
              border: "1px solid #cbd5e1",
              padding: 16,
              fontFamily: "monospace",
              fontSize: 14
            }}
          />
          <button
            disabled={loading}
            onClick={handleAnalyze}
            style={{
              width: 170,
              border: "none",
              borderRadius: 10,
              background: "#2563eb",
              color: "#fff",
              cursor: "pointer",
              fontWeight: 600,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              gap: 10
            }}
          >
            {loading ? (
              <Loader2
                className="animate-spin"
                size={18}
              />
            ) : (
              <Send size={18} />
            )}
            Analyse
          </button>
        </div>
      </div>
    </>
  );

  const renderHistory = () => (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        padding: 30
      }}
    >
      <h2
        style={{
          marginTop: 0,
          display: "flex",
          alignItems: "center",
          gap: 10
        }}
      >
        <Database size={24} />
        Prediction History
      </h2>
      {history.length === 0 ? (
        <div
          style={{
            marginTop: 40,
            color: "#64748b"
          }}
        >
          No predictions available.
        </div>
      ) : (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 18
          }}
        >
          {history.map((item, index) => (
            <div
              key={index}
              style={{
                background: "#fff",
                border: "1px solid #e5e7eb",
                borderRadius: 12,
                padding: 20
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: 15
                }}
              >
                <div>
                  <div
                    style={{
                      fontWeight: 700,
                      color: predictionColour(item.classification_type)
                    }}
                  >
                    {item.prediction}
                  </div>
                  <div
                    style={{
                      color: "#64748b",
                      fontSize: 13
                    }}
                  >
                    {item.classification_type}
                  </div>
                </div>
                <div
                  style={{
                    textAlign: "right"
                  }}
                >
                  <div>
                    {pct(item.confidence)}%
                  </div>
                  <div
                    style={{
                      color: "#64748b",
                      fontSize: 12
                    }}
                  >
                    {item.timestamp}
                  </div>
                </div>
              </div>
              <pre
                style={{
                  margin: 0,
                  background: "#f8fafc",
                  borderRadius: 8,
                  padding: 14,
                  fontSize: 12,
                  overflowX: "auto"
                }}
              >
                {item.rawLog}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderDashboard = () => (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        padding: 30
      }}
    >
      <h2
        style={{
          marginTop: 0,
          display: "flex",
          gap: 10,
          alignItems: "center"
        }}
      >
        <BarChart3 size={24} />
        Behaviour Dashboard
      </h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4,1fr)",
          gap: 20
        }}
      >
        <InfoCard
          title="Normal"
          value={dashboard.normal}
          icon={<ShieldCheck color="#10b981" />}
        />
        <InfoCard
          title="Anomalies"
          value={dashboard.anomaly}
          icon={<ShieldAlert color="#ef4444" />}
        />
        <InfoCard
          title="Pending"
          value={dashboard.pending}
          icon={<Clock color="#f59e0b" />}
        />
        <InfoCard
          title="Avg Confidence"
          value={`${dashboard.averageConfidence}%`}
          icon={<Cpu color="#2563eb" />}
        />
      </div>
      <div
        style={{
          marginTop: 30,
          background: "#fff",
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          padding: 25
        }}
      >
        <h3
          style={{
            marginTop: 0
          }}
        >
          Backend Status
        </h3>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4,1fr)",
            gap: 18,
            marginTop: 20
          }}
        >
          <InfoCard
            title="Backend"
            value={backendOnline ? "Online" : "Offline"}
            icon={
              <Server
                color={backendOnline ? "#10b981" : "#ef4444"}
              />
            }
          />
          <InfoCard
            title="Model"
            value={modelVersion}
            icon={<Cpu />}
          />
          <InfoCard
            title="Sequence"
            value={sequenceLength}
            icon={<Activity />}
          />
          <InfoCard
            title="Requests"
            value={requestsProcessed}
            icon={<Database />}
          />
        </div>
        <div
          style={{
            marginTop: 20,
            display: "grid",
            gridTemplateColumns: "repeat(2,1fr)",
            gap: 20
          }}
        >
          <InfoCard
            title="Tracked Entities"
            value={trackedEntities}
          />
          <InfoCard
            title="Cached Predictions"
            value={backendStatus ? backendStatus.cached_predictions : 0}
          />
        </div>
      </div>
    </div>
  );

  const renderSettings = () => (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        padding: 30
      }}
    >
      <h2
        style={{
          marginTop: 0,
          display: "flex",
          gap: 10,
          alignItems: "center"
        }}
      >
        <Sliders size={24} />
        Engine Settings
      </h2>
      <div
        style={{
          maxWidth: 700,
          background: "#fff",
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          padding: 25
        }}
      >
        <label>
          Confidence Threshold
        </label>
        <input
          type="range"
          min="50"
          max="99"
          value={threshold}
          onChange={(e) => setThreshold(e.target.value)}
          style={{
            width: "100%",
            marginTop: 10
          }}
        />
        <div
          style={{
            marginBottom: 25
          }}
        >
          {threshold}%
        </div>
        <label>
          Explainer
        </label>
        <select
          value={explainer}
          onChange={(e) => setExplainer(e.target.value)}
          style={{
            width: "100%",
            padding: 12,
            marginTop: 10,
            borderRadius: 8
          }}
        >
          <option>
            SHAP
          </option>
        </select>
        <div
          style={{
            display: "flex",
            gap: 15,
            marginTop: 30
          }}
        >
          <button
            style={{
              border: "none",
              background: "#2563eb",
              color: "#fff",
              padding: "12px 25px",
              borderRadius: 8,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 10
            }}
          >
            <Save size={18} />
            Save
          </button>
          <button
            onClick={resetBackend}
            style={{
              border: "none",
              background: "#ef4444",
              color: "#fff",
              padding: "12px 25px",
              borderRadius: 8,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 10
            }}
          >
            <RefreshCw size={18} />
            Reset Backend
          </button>
        </div>
      </div>
    </div>
  );

  function InfoCard({ title, value, icon }) {
    return (
      <div
        style={{
          background: "#fff",
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          padding: 20,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxShadow: "0 2px 6px rgba(0,0,0,0.04)"
        }}
      >
        <div>
          <div
            style={{
              color: "#64748b",
              fontSize: 13,
              marginBottom: 8
            }}
          >
            {title}
          </div>
          <div
            style={{
              fontSize: 24,
              fontWeight: 700,
              color: "#0f172a"
            }}
          >
            {value}
          </div>
        </div>
        <div
          style={{
            background: "#f8fafc",
            borderRadius: 10,
            padding: 12
          }}
        >
          {icon || <Activity size={22} color="#2563eb" />}
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        width: "100vw",
        height: "100vh",
        overflow: "hidden",
        background: "#f8fafc",
        fontFamily: "Inter, sans-serif"
      }}
    >
      <aside
        style={{
          width: 270,
          background: "#0f172a",
          color: "#fff",
          display: "flex",
          flexDirection: "column"
        }}
      >
        <div
          style={{
            padding: 25,
            borderBottom: "1px solid #1e293b",
            display: "flex",
            alignItems: "center",
            gap: 12
          }}
        >
          <ShieldAlert
            size={30}
            color="#38bdf8"
          />
          <div>
            <div
              style={{
                fontWeight: 700,
                fontSize: 19
              }}
            >
              ThreatVision
            </div>
            <div
              style={{
                fontSize: 12,
                color: "#94a3b8"
              }}
            >
              Behaviour IDS
            </div>
          </div>
        </div>
        <nav
          style={{
            padding: 18,
            display: "flex",
            flexDirection: "column",
            gap: 8,
            flex: 1
          }}
        >
          <div onClick={() => setCurrentView("live")}>
            <SidebarItem
              active={currentView === "live"}
              icon={<LayoutDashboard size={18} />}
              label="Live Analysis"
            />
          </div>
          <div onClick={() => setCurrentView("dashboard")}>
            <SidebarItem
              active={currentView === "dashboard"}
              icon={<BarChart3 size={18} />}
              label="Dashboard"
            />
          </div>
          <div onClick={() => setCurrentView("history")}>
            <SidebarItem
              active={currentView === "history"}
              icon={<FileText size={18} />}
              label="History"
            />
          </div>
          <div onClick={() => setCurrentView("settings")}>
            <SidebarItem
              active={currentView === "settings"}
              icon={<Settings size={18} />}
              label="Settings"
            />
          </div>
        </nav>
        <div
          style={{
            padding: 20,
            borderTop: "1px solid #1e293b",
            fontSize: 13
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              color: backendOnline ? "#10b981" : "#ef4444"
            }}
          >
            <Activity size={15} />
            {backendOnline ? "Backend Online" : "Backend Offline"}
          </div>
          <div
            style={{
              marginTop: 8,
              color: "#94a3b8"
            }}
          >
            Model {modelVersion}
          </div>
        </div>
      </aside>
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden"
        }}
      >
        <header
          style={{
            height: 70,
            background: "#fff",
            borderBottom: "1px solid #e5e7eb",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "0 30px"
          }}
        >
          <div>
            <div
              style={{
                fontSize: 22,
                fontWeight: 700,
                color: "#0f172a",
                textTransform: "capitalize"
              }}
            >
              {currentView}
            </div>
            <div
              style={{
                color: "#64748b",
                fontSize: 13
              }}
            >
              Sequence-based Behaviour Intrusion Detection
            </div>
          </div>
          <div
            style={{
              display: "flex",
              gap: 12,
              alignItems: "center"
            }}
          >
            <Server
              size={18}
              color={backendOnline ? "#10b981" : "#ef4444"}
            />
            <span>
              {backendOnline ? "Connected" : "Disconnected"}
            </span>
          </div>
        </header>
        {currentView === "live" && renderLiveAnalysis()}
        {currentView === "dashboard" && renderDashboard()}
        {currentView === "history" && renderHistory()}
        {currentView === "settings" && renderSettings()}
        <footer
          style={{
            background: "#fff",
            borderTop: "1px solid #e5e7eb",
            padding: 15,
            textAlign: "center",
            color: "#64748b",
            fontSize: 13
          }}
        >
          © 2026 ThreatVision • Behaviour-Based Intrusion Detection System • Developed by Aayush Ojha
        </footer>
      </div>
    </div>
  );
}

function SidebarItem({
  icon,
  label,
  active
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "12px 16px",
        borderRadius: 10,
        cursor: "pointer",
        transition: "0.2s",
        background: active ? "#1e293b" : "transparent",
        color: active ? "#38bdf8" : "#cbd5e1"
      }}
    >
      {icon}
      <span
        style={{
          fontSize: 14,
          fontWeight: 500
        }}
      >
        {label}
      </span>
    </div>
  );
}

export default App;