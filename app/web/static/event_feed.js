// T22 live event feed: renders background + focal pipeline events as they
// arrive over Server-Sent Events. No WebSockets, no polling — one EventSource
// connection per page load.
(function () {
  "use strict";

  const DECISION_BADGE = {
    allow: "decision-allow",
    allow_with_logging: "decision-info",
    escalate: "decision-warn",
    block: "decision-block",
    fail_closed: "decision-block",
    require_evidence: "decision-warn",
    modify: "decision-warn",
  };

  function badgeClass(decision) {
    return DECISION_BADGE[decision] || "decision-info";
  }

  function renderBackgroundRow(payload) {
    const row = document.createElement("div");
    row.className = "event-row event-row-background";
    row.innerHTML =
      '<span class="event-row-index">' + payload.event_index + "/" + payload.total_events + "</span>" +
      '<span class="event-row-summary">' + escapeHtml(payload.action_summary) + "</span>" +
      '<span class="event-badge ' + badgeClass(payload.decision) + '">' + escapeHtml(payload.decision) + "</span>";
    return row;
  }

  function renderTraceStage(stage) {
    const card = document.createElement("div");
    card.className = "trace-stage-card";
    const inputs = JSON.stringify(stage.inputs_summary, null, 0);
    const outputs = JSON.stringify(stage.outputs_summary, null, 0);
    card.innerHTML =
      '<div class="trace-stage-header"><strong>' + escapeHtml(stage.stage_name) + '</strong>' +
      '<span class="card-note">' + stage.duration_ms.toFixed(1) + ' ms</span></div>' +
      '<p class="card-note">Consumed: <span class="mono">' + escapeHtml(inputs) + '</span></p>' +
      '<p class="card-note">Produced: <span class="mono">' + escapeHtml(outputs) + '</span></p>';
    return card;
  }

  function renderFocalRow(payload) {
    const wrapper = document.createElement("div");
    wrapper.className = "event-row event-row-focal " + badgeClass(payload.decision);

    const summary = document.createElement("button");
    summary.type = "button";
    summary.className = "event-row-focal-summary";
    summary.innerHTML =
      '<span class="event-row-index">' + payload.event_index + "/" + payload.total_events + " — FOCAL</span>" +
      '<span class="event-row-summary">' + escapeHtml(payload.action_summary) + "</span>" +
      '<span class="event-badge ' + badgeClass(payload.decision) + '">' +
      escapeHtml(payload.decision) + (payload.control_id ? " — " + escapeHtml(payload.control_id) : "") +
      "</span>";

    const details = document.createElement("div");
    details.className = "trace-timeline";
    details.style.display = "block";
    (payload.trace || []).forEach(function (stage) {
      details.appendChild(renderTraceStage(stage));
    });

    summary.addEventListener("click", function () {
      details.style.display = details.style.display === "none" ? "block" : "none";
    });

    wrapper.appendChild(summary);
    wrapper.appendChild(details);
    return wrapper;
  }

  function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = String(value);
    return div.innerHTML;
  }

  function padNumber(value, width) {
    const text = String(value);
    return text.length >= width ? text : "0".repeat(width - text.length) + text;
  }

  function padLabel(value, width) {
    const text = String(value);
    return text.length >= width ? text : text + " ".repeat(width - text.length);
  }

  function appendTerminalLine(terminalBody, text, className) {
    if (terminalBody.childNodes.length > 0) {
      terminalBody.appendChild(document.createTextNode("\n"));
    }
    const line = document.createElement("span");
    line.className = className;
    line.textContent = text;
    terminalBody.appendChild(line);
    terminalBody.scrollTop = terminalBody.scrollHeight;
  }

  function appendTerminalEvent(terminalBody, payload) {
    const index = payload.is_focal ? "FOCAL" : padNumber(payload.event_index, 2);
    const text =
      "[" + index + "/" + payload.total_events + "] " +
      padLabel(payload.decision.toUpperCase(), 10) +
      payload.action_summary +
      (payload.control_id ? " (" + payload.control_id + ")" : "");
    const className = "terminal-line " + badgeClass(payload.decision) + (payload.is_focal ? " terminal-line-focal" : "");
    appendTerminalLine(terminalBody, text, className);
  }

  function init() {
    const section = document.getElementById("event-feed-section");
    if (!section) {
      return;
    }
    const list = document.getElementById("event-feed-list");
    const statusEl = document.getElementById("event-feed-status");
    const terminalBody = document.getElementById("event-feed-terminal-body");
    const streamUrl = section.dataset.streamUrl;

    if (terminalBody) {
      appendTerminalLine(terminalBody, "Connecting to " + streamUrl + " ...", "terminal-line terminal-line-status");
    }

    const source = new EventSource(streamUrl);

    source.onmessage = function (event) {
      const payload = JSON.parse(event.data);
      if (terminalBody) {
        appendTerminalEvent(terminalBody, payload);
      }
      if (payload.is_focal) {
        list.appendChild(renderFocalRow(payload));
        statusEl.textContent = "Focal event landed: " + payload.decision + (payload.control_id ? " (" + payload.control_id + ")" : "") + ".";
        if (terminalBody) {
          appendTerminalLine(terminalBody, "-- pipeline complete --", "terminal-line terminal-line-status");
        }
        source.close();
      } else {
        list.appendChild(renderBackgroundRow(payload));
        statusEl.textContent = "Streaming background event " + payload.event_index + " of " + payload.total_events + "...";
      }
    };

    source.onerror = function () {
      statusEl.textContent = "Live feed connection closed.";
      if (terminalBody) {
        appendTerminalLine(terminalBody, "-- connection closed --", "terminal-line terminal-line-status");
      }
      source.close();
    };
  }

  document.addEventListener("DOMContentLoaded", init);
})();
