import kr.dogfoot.hwplib.reader.HWPReader;
import kr.dogfoot.hwplib.object.HWPFile;
import kr.dogfoot.hwplib.object.docinfo.BorderFill;
import kr.dogfoot.hwplib.object.docinfo.borderfill.fillinfo.FillInfo;
import kr.dogfoot.hwplib.object.docinfo.borderfill.fillinfo.FillType;
import kr.dogfoot.hwplib.object.docinfo.borderfill.fillinfo.PatternFill;
import kr.dogfoot.hwplib.object.docinfo.borderfill.fillinfo.GradientFill;
import kr.dogfoot.hwplib.object.etc.Color4Byte;

import java.util.List;

/**
 * Dumps DocInfo BorderFill fill information as JSON so a Python post-processor
 * can patch HWPX borderFills that hwp2hwpx produces without a {@code <hc:fillBrush>}.
 *
 * Output format: JSON array of {id, type, bgColor, patternColor, patternType}
 * or {id, type, gradientType, angle, colors[]} per borderFill.
 * The {@code id} is 1-based to match the {@code <hh:borderFill id>} scheme in HWPX.
 */
public class HwpFillDump {
    public static void main(String[] args) throws Exception {
        if (args.length < 1) {
            System.err.println("Usage: HwpFillDump <input.hwp>");
            System.exit(1);
        }
        HWPFile hwp = HWPReader.fromFile(args[0]);
        List<BorderFill> bfs = hwp.getDocInfo().getBorderFillList();

        StringBuilder sb = new StringBuilder();
        sb.append("[");
        for (int i = 0; i < bfs.size(); i++) {
            if (i > 0) sb.append(",");
            sb.append(borderFillJson(i + 1, bfs.get(i)));
        }
        sb.append("]");
        System.out.println(sb);
    }

    private static String borderFillJson(int id, BorderFill bf) {
        StringBuilder sb = new StringBuilder();
        sb.append("{\"id\":").append(id);
        FillInfo fi = bf.getFillInfo();
        if (fi == null) {
            sb.append(",\"type\":\"none\"}");
            return sb.toString();
        }
        FillType ft = fi.getType();
        boolean hasPattern = ft != null && ft.hasPatternFill();
        boolean hasGradient = ft != null && ft.hasGradientFill();
        boolean hasImage = ft != null && ft.hasImageFill();

        if (hasPattern && fi.getPatternFill() != null) {
            PatternFill pf = fi.getPatternFill();
            sb.append(",\"type\":\"color\"");
            sb.append(",\"bgColor\":\"").append(hex(pf.getBackColor())).append("\"");
            sb.append(",\"patternColor\":\"").append(hex(pf.getPatternColor())).append("\"");
            sb.append(",\"patternType\":\"").append(safeName(pf.getPatternType())).append("\"");
        } else if (hasGradient && fi.getGradientFill() != null) {
            GradientFill gf = fi.getGradientFill();
            sb.append(",\"type\":\"gradient\"");
            sb.append(",\"gradientType\":\"").append(safeName(gf.getGradientType())).append("\"");
            sb.append(",\"angle\":").append(gf.getStartAngle());
            sb.append(",\"centerX\":").append(gf.getCenterX());
            sb.append(",\"centerY\":").append(gf.getCenterY());
            sb.append(",\"blur\":").append(gf.getBlurringDegree());
            sb.append(",\"colors\":[");
            List<Color4Byte> cs = gf.getColorList();
            for (int k = 0; k < cs.size(); k++) {
                if (k > 0) sb.append(",");
                sb.append("\"").append(hex(cs.get(k))).append("\"");
            }
            sb.append("]");
        } else if (hasImage) {
            sb.append(",\"type\":\"image\"");
        } else {
            sb.append(",\"type\":\"none\"");
        }
        sb.append("}");
        return sb.toString();
    }

    private static String hex(Color4Byte c) {
        if (c == null) return "#000000";
        return String.format("#%02X%02X%02X", c.getR() & 0xFF, c.getG() & 0xFF, c.getB() & 0xFF);
    }

    private static String safeName(Object o) {
        return o == null ? "" : o.toString();
    }
}
