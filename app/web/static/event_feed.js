// T22 live event feed: renders background + focal pipeline events as they
// arrive over Server-Sent Events. No WebSockets, no polling — one EventSource
// connection per page load.
(function () {
  "use strict";

  var DECISION_BADGE = {
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
    var row = document.createElement("div");
    row.className = "event-row event-row-background";
    row.innerHTML =
      '<span class="event-row-index">' + payload.event_index + "/" + payload.total_events + "</span>" +
      '<span class="event-row-summary">' + escapeHtml(payload.action_summary) + "</span>" +
      '<span class="event-badge ' + badgeClass(payload.decision) + '">' + escapeHtml(payload.decision) + "</span>";
    return row;
  }

  function renderTraceStage(stage) {
    var card = document.createElement("div");
    card.className = "trace-stage-card";
    var inputs = JSON.stringify(stage.inputs_summary, null, 0);
    var outputs = JSON.stringify(stage.outputs_summary, null, 0);
    card.innerHTML =
      '<div class="trace-stage-header"><strong>' + escapeHtml(stage.stage_name) + '</strong>' +
      '<span class="card-note">' + stage.duration_ms.toFixed(1) + ' ms</span></div>' +
      '<p class="card-note">Consumed: <span class="mono">' + escapeHtml(inputs) + '</span></p>' +
      '<p class="card-note">Produced: <span class="mono">' + escapeHtml(outputs) + '</span></p>';
    return card;
  }

  function renderFocalRow(payload) {
    var wrapper = document.createElement("div");
    wrapper.className = "event-row event-row-focal " + badgeClass(payload.decision);

    var summary = document.createElement("button");
    summary.type = "button";
    summary.className = "event-row-focal-summary";
    summary.innerHTML =
      '<span class="event-row-index">' + payload.event_index + "/" + payload.total_events + " — FOCAL</span>" +
      '<span class="event-row-summary">' + escapeHtml(payload.action_summary) + "</span>" +
      '<span class="event-badge ' + badgeClass(payload.decision) + '">' +
      escapeHtml(payload.decision) + (payload.control_id ? " — " + escapeHtml(payload.control_id) : "") +
      "</span>";

    var details = document.createElement("div");
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
    var div = document.createElement("div");
    div.textContent = String(value);
    return div.innerHTML;
  }

  function init() {
    var section = document.getElementById("event-feed-section");
    if (!section) {
      return;
    }
    var list = document.getElementById("event-feed-list");
    var statusEl = document.getElementById("event-feed-status");
    var streamUrl = section.getAttribute("data-stream-url");

    var source = new EventSource(streamUrl);

    source.onmessage = function (event) {
      var payload = JSON.parse(event.data);
      if (payload.is_focal) {
        list.appendChild(renderFocalRow(payload));
        statusEl.textContent = "Focal event landed: " + payload.decision + (payload.control_id ? " (" + payload.control_id + ")" : "") + ".";
        source.close();
      } else {
        list.appendChild(renderBackgroundRow(payload));
        statusEl.textContent = "Streaming background event " + payload.event_index + " of " + payload.total_events + "...";
      }
    };

    source.onerror = function () {
      statusEl.textContent = "Live feed connection closed.";
      source.close();
    };
  }

  document.addEventListener("DOMContentLoaded", init);
})();
