/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class SkyDocumentListRenderer extends ListRenderer {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.actionService = useService("action");
    }

    /**
     * @override
     */
    onAttached() {
        super.onAttached();
        this._setupDragAndDrop();
    }

    /**
     * Setup drag and drop events
     * @private
     */
    _setupDragAndDrop() {
        const $el = $(this.el);
        $el.on('dragover', this._onDragOver.bind(this));
        $el.on('dragleave', this._onDragLeave.bind(this));
        $el.on('drop', this._onDrop.bind(this));
    }

    /**
     * Handle dragover event
     * @private
     * @param {Event} event
     */
    _onDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        $(this.el).addClass('sky_document_dragover');
    }

    /**
     * Handle dragleave event
     * @private
     * @param {Event} event
     */
    _onDragLeave(event) {
        event.preventDefault();
        event.stopPropagation();
        $(this.el).removeClass('sky_document_dragover');
    }

    /**
     * Handle drop event
     * @private
     * @param {Event} event
     */
    _onDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        $(this.el).removeClass('sky_document_dragover');

        // Get the files from the drop event
        const files = event.originalEvent.dataTransfer.files;
        if (!files || !files.length) {
            return;
        }

        this._uploadFiles(files);
    }

    /**
     * Upload files to the server
     * @private
     * @param {FileList} files
     */
    async _uploadFiles(files) {
        const promises = [];
        const context = this.props.context || {};

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const reader = new FileReader();
            
            promises.push(new Promise((resolve, reject) => {
                reader.onload = async () => {
                    try {
                        const base64Data = reader.result.split(',')[1];
                        const vals = {
                            name: file.name,
                            file: base64Data,
                            file_name: file.name,
                        };
                        
                        // Add partner_id and folder_id from context if available
                        if (context.default_partner_id) {
                            vals.partner_id = context.default_partner_id;
                        }
                        if (context.default_folder_id) {
                            vals.folder_id = context.default_folder_id;
                        }
                        
                        const documentId = await this.orm.create('sky.document', [vals]);
                        resolve(documentId);
                    } catch (error) {
                        reject(error);
                    }
                };
                reader.onerror = reject;
                reader.readAsDataURL(file);
            }));
        }

        try {
            await Promise.all(promises);
            this.notification.add(_t("Files uploaded successfully"), {
                type: "success",
            });
            this.props.list.load();
        } catch (error) {
            this.notification.add(_t("Error uploading files"), {
                type: "danger",
            });
            console.error("Error uploading files:", error);
        }
    }
}

registry.category("views").add("sky_document_list", {
    ...listView,
    Renderer: SkyDocumentListRenderer,
});