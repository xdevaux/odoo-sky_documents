/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useRef } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

/**
 * Document Viewer Dialog
 * 
 * A dialog component that displays a document in an iframe
 */
export class SkyDocumentViewerDialog extends Dialog {
    setup() {
        super.setup();
        this.iframeRef = useRef("iframe");

        onMounted(() => {
            // Set the iframe source to the document URL
            if (this.props.url) {
                this.iframeRef.el.src = this.props.url;
            }
        });
    }
}
SkyDocumentViewerDialog.template = "sky_documents.DocumentViewerDialog";
SkyDocumentViewerDialog.size = "xl"; // Extra large dialog

/**
 * Document Viewer Action
 * 
 * A client action that opens a document in a dialog
 */
export class SkyDocumentViewerAction extends Component {
    setup() {
        this.dialogService = useService("dialog");
        this.actionService = useService("action");

        onMounted(() => {
            this._openDocumentDialog();
        });
    }

    /**
     * Open the document viewer dialog
     * @private
     */
    _openDocumentDialog() {
        // Get URL from props.params (passed from the server action)
        const url = this.props.params?.url;
        if (!url) {
            return;
        }

        this.dialogService.add(SkyDocumentViewerDialog, {
            url: url,
            title: this.props.params?.title || "Document Viewer",
        }, {
            onClose: () => {
                // Return to the previous view when the dialog is closed
                if (this.props.onClose) {
                    this.props.onClose();
                } else {
                    this.actionService.doAction({ type: "ir.actions.act_window_close" });
                }
            }
        });
    }
}
SkyDocumentViewerAction.template = "sky_documents.DocumentViewerAction";

// Register the client action
registry.category("actions").add("sky_document_viewer", SkyDocumentViewerAction);
