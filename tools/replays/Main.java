package skadistats.clarity.examples.flyextract;

import java.io.PrintWriter;
import java.util.Locale;
import skadistats.clarity.event.Insert;
import skadistats.clarity.model.Entity;
import skadistats.clarity.model.CombatLogEntry;
import skadistats.clarity.processor.gameevents.OnCombatLogEntry;
import skadistats.clarity.processor.entities.Entities;
import skadistats.clarity.processor.entities.UsesEntities;
import skadistats.clarity.processor.reader.OnTickEnd;
import skadistats.clarity.processor.runner.Context;
import skadistats.clarity.processor.runner.SimpleRunner;
import skadistats.clarity.source.MappedFileSource;

/** First-stage own-hero telemetry. Does not infer clicks or expose enemy fog data. */
@UsesEntities
public class Main {
    @Insert private Entities entities;
    private PrintWriter out;
    private int playerIndex;
    private boolean dumped=false;
    @OnCombatLogEntry public void combat(Context ctx,CombatLogEntry e) {
        // Purchase logs identify the buyer in target, not attacker.
        if(e.getType().name().equals("DOTA_COMBATLOG_PURCHASE") &&
           "npc_dota_hero_nevermore".equals(e.getTargetName())) {
            String item=e.getValueName();
            if(item!=null && item.matches("item_[a-z0-9_]+"))
                out.printf(Locale.ROOT,"{\"event\":\"purchase\",\"tick\":%d,\"item\":\"%s\"}%n",ctx.getTick(),item);
            return;
        }
        if(!"npc_dota_hero_nevermore".equals(e.getAttackerName()) || e.isAttackerIllusion())return;
        String name=e.getInflictorName();
        if(e.getType().name().equals("DOTA_COMBATLOG_ABILITY") && name!=null && name.startsWith("nevermore_"))
            out.printf(Locale.ROOT,"{\"event\":\"cast\",\"tick\":%d,\"ability\":\"%s\"}%n",ctx.getTick(),name);
        if(e.getType().name().equals("DOTA_COMBATLOG_DAMAGE") && (name==null || name.isEmpty() || name.equals("dota_unknown")))
            out.printf(Locale.ROOT,"{\"event\":\"attack_activity_proxy\",\"tick\":%d}%n",ctx.getTick());
    }
    private static Number number(Entity e,String field) {
        Object v=e.getProperty(field);
        if (!(v instanceof Number)) throw new IllegalArgumentException("Missing numeric field: "+field);
        return (Number)v;
    }
    @OnTickEnd public void tick(Context ctx,boolean synthetic) {
        if (synthetic || ctx.getTick()%30!=0) return;
        Entity resource=entities.getByDtName("CDOTA_PlayerResource");
        if(resource==null)return;
        String field=String.format("m_vecPlayerTeamData.%04d.m_hSelectedHero",playerIndex);
        Object handle=resource.getProperty(field);
        if(!(handle instanceof Integer))return;
        Entity h=entities.getByHandle((Integer)handle);
        if(h==null || !h.getDtClass().getDtName().contains("Nevermore"))return;
        if(!dumped){System.err.println(h);dumped=true;}
        double x=number(h,"CBodyComponent.m_cellX").doubleValue()*128+number(h,"CBodyComponent.m_vecX").doubleValue()-16384;
        double y=number(h,"CBodyComponent.m_cellY").doubleValue()*128+number(h,"CBodyComponent.m_vecY").doubleValue()-16384;
        out.printf(Locale.ROOT,"{\"tick\":%d,\"x\":%.4f,\"y\":%.4f,\"hp\":%s,\"max_hp\":%s,\"mana\":%s,\"max_mana\":%s,\"life_state\":%s,\"level\":%s}%n",
            ctx.getTick(),x,y,number(h,"m_iHealth"),number(h,"m_iMaxHealth"),number(h,"m_flMana"),number(h,"m_flMaxMana"),number(h,"m_lifeState"),number(h,"m_iCurrentLevel"));
    }
    public static void main(String[] args)throws Exception {
        Main p=new Main();p.playerIndex=Integer.parseInt(args[1]);
        try(PrintWriter out=new PrintWriter(args[2]);MappedFileSource source=new MappedFileSource(args[0])){
            p.out=out;new SimpleRunner(source).runWith(p);
        }
    }
}
