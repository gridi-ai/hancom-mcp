import kr.dogfoot.hwplib.reader.HWPReader;
import kr.dogfoot.hwplib.object.HWPFile;
import kr.dogfoot.hwplib.object.bodytext.Section;
import kr.dogfoot.hwplib.object.bodytext.paragraph.Paragraph;
import kr.dogfoot.hwplib.object.bodytext.control.Control;
import kr.dogfoot.hwplib.object.bodytext.control.ControlTable;
import kr.dogfoot.hwplib.object.bodytext.control.ControlType;
import kr.dogfoot.hwplib.object.bodytext.control.table.Row;
import kr.dogfoot.hwplib.object.bodytext.control.table.Cell;
import kr.dogfoot.hwplib.object.bodytext.control.table.ListHeaderForCell;
import kr.dogfoot.hwplib.object.bodytext.control.table.ZoneInfo;

import java.util.List;

/**
 * Dumps every table control found in every section as JSON:
 *   [{"id": <HWPX tbl id>, "section": <idx>, "cells": [{row, col, rowSpan,
 *    colSpan, bf}, ...]}, ...]
 *
 * The per-cell {@code bf} is the borderFillId stored in the HWP binary. HWPX's
 * {@code <hp:tc borderFillIDRef>} uses the same numbering; discrepancies between
 * the two are the artefact hwp2hwpx produces when it loses cell-level border
 * fill assignments. The Python side can then overwrite each cell's attribute
 * with the authoritative value.
 */
public class HwpTableDump {
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("Usage: HwpTableDump <input.hwp>");
            System.exit(1);
        }
        HWPFile hwp = HWPReader.fromFile(args[0]);
        StringBuilder sb = new StringBuilder();
        sb.append("[");
        boolean first = true;
        List<Section> sections = hwp.getBodyText().getSectionList();
        for (int si = 0; si < sections.size(); si++) {
            for (Paragraph p : sections.get(si).getParagraphs()) {
                if (p.getControlList() == null) continue;
                for (Control ctrl : p.getControlList()) {
                    if (ctrl.getType() == ControlType.Table) {
                        if (!first) sb.append(",");
                        first = false;
                        sb.append(tableJson((ControlTable) ctrl, si));
                    }
                    walkNestedTables(ctrl, si, sb, first);
                    if (!first && sb.charAt(sb.length() - 1) != '[') first = false;
                }
            }
        }
        sb.append("]");
        System.out.println(sb);
    }

    private static void walkNestedTables(Control ctrl, int si, StringBuilder sb, boolean firstRef) {
        if (ctrl.getType() != ControlType.Table) return;
        ControlTable tbl = (ControlTable) ctrl;
        for (Row row : tbl.getRowList()) {
            for (Cell cell : row.getCellList()) {
                if (cell.getParagraphList() == null) continue;
                for (Paragraph p : cell.getParagraphList()) {
                    if (p.getControlList() == null) continue;
                    for (Control inner : p.getControlList()) {
                        if (inner.getType() == ControlType.Table) {
                            sb.append(",");
                            sb.append(tableJson((ControlTable) inner, si));
                        }
                        walkNestedTables(inner, si, sb, firstRef);
                    }
                }
            }
        }
    }

    private static String tableJson(ControlTable tbl, int si) {
        StringBuilder sb = new StringBuilder();
        long id = tbl.getHeader().getInstanceId() & 0xFFFFFFFFL;
        sb.append("{\"id\":").append(id);
        sb.append(",\"section\":").append(si);
        sb.append(",\"cells\":[");
        boolean first = true;
        for (Row row : tbl.getRowList()) {
            for (Cell cell : row.getCellList()) {
                if (!first) sb.append(",");
                first = false;
                ListHeaderForCell h = cell.getListHeader();
                sb.append("{\"row\":").append(h.getRowIndex());
                sb.append(",\"col\":").append(h.getColIndex());
                sb.append(",\"rowSpan\":").append(h.getRowSpan());
                sb.append(",\"colSpan\":").append(h.getColSpan());
                sb.append(",\"bf\":").append(h.getBorderFillId());
                sb.append("}");
            }
        }
        sb.append("],\"zones\":[");
        boolean firstZ = true;
        if (tbl.getTable() != null && tbl.getTable().getZoneInfoList() != null) {
            for (ZoneInfo z : tbl.getTable().getZoneInfoList()) {
                if (!firstZ) sb.append(",");
                firstZ = false;
                sb.append("{\"startRow\":").append(z.getStartRow());
                sb.append(",\"startCol\":").append(z.getStartColumn());
                sb.append(",\"endRow\":").append(z.getEndRow());
                sb.append(",\"endCol\":").append(z.getEndColumn());
                sb.append(",\"bf\":").append(z.getBorderFillId());
                sb.append("}");
            }
        }
        sb.append("]}");
        return sb.toString();
    }
}
