"""
Demo dataset seed — creates a sample project with taxa, locations,
sampling events, replicates, and occurrence records to validate all flows.
"""
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import (
    Location, Method, OccurrenceRecord, Project,
    Replicate, SamplingEvent, Taxon,
)


TAXA = [
    ("Coleoptera", "order", None, None),
    ("Chrysomelidae", "family", "Coleoptera", "Escarabajos de hojas"),
    ("Curculionidae", "family", "Coleoptera", "Gorgojos"),
    ("Chrysomela populi", "species", "Chrysomelidae", None),
    ("Curculio glandium", "species", "Curculionidae", None),
    ("Chrysomelidae sp. 1", "morphospecies", "Chrysomelidae", None),
    ("Chrysomelidae sp. 2", "morphospecies", "Chrysomelidae", None),
    ("Ephemeroptera", "order", None, None),
    ("Baetidae", "family", "Ephemeroptera", "Efímeras pequeñas"),
    ("Baetis sp. 1", "morphospecies", "Baetidae", None),
    ("Baetis sp. 2", "morphospecies", "Baetidae", None),
    ("Diptera", "order", None, None),
    ("Chironomidae", "family", "Diptera", "Mosquitos de agua"),
    ("Chironomus sp. 1", "morphospecies", "Chironomidae", None),
]

LOCATIONS = [
    ("Cuenca Alta", None, "region", -17.5, -66.2, 3800),
    ("Estación Norte", "Cuenca Alta", "locality", -17.48, -66.18, 3820),
    ("Punto N1", "Estación Norte", "point", -17.481, -66.183, 3815),
    ("Punto N2", "Estación Norte", "point", -17.479, -66.181, 3825),
    ("Estación Sur", "Cuenca Alta", "locality", -17.52, -66.22, 3750),
    ("Punto S1", "Estación Sur", "point", -17.521, -66.221, 3748),
]

METHODS = [
    ("RED", "Red de barrido", "Golpeo y barrido de vegetación con red entomológica"),
    ("TRAMPA_CAIDA", "Trampa de caída (pitfall)", "Trampas de plástico enterradas a nivel del suelo"),
    ("TRANSECTO", "Transecto visual", "Observación directa a lo largo de transecto de 50m"),
    ("SURBER", "Red Surber", "Muestreo bentónico con red Surber 30x30cm"),
]


def seed(db: Session | None = None):
    close_after = db is None
    if db is None:
        db = SessionLocal()

    try:
        if db.query(Project).count() > 0:
            print("Seed data already exists — skipping.")
            return

        # Project
        proj = Project(
            name="Demo: Entomofauna Cuenca Alta",
            description="Proyecto de demostración con datos de insectos acuáticos y terrestres.",
            photos_root_path=None,
        )
        db.add(proj)
        db.flush()

        # Methods
        method_map = {}
        for code, label, desc in METHODS:
            m = Method(project_id=proj.id, code=code, label=label, description=desc)
            db.add(m)
            db.flush()
            method_map[code] = m

        # Locations
        loc_map = {}
        for name, parent_name, loc_type, lat, lon, alt in LOCATIONS:
            parent_id = loc_map[parent_name].id if parent_name else None
            l = Location(
                project_id=proj.id,
                parent_location_id=parent_id,
                name=name,
                type=loc_type,
                latitude=lat,
                longitude=lon,
                altitude=alt,
            )
            db.add(l)
            db.flush()
            loc_map[name] = l

        # Taxa
        taxon_map = {}
        alias_counter: dict = {}
        for sci_name, rank, parent_name, common in TAXA:
            parent_id = taxon_map[parent_name].id if parent_name else None
            # Auto alias
            prefix = "Morfo" if "morphospecies" in rank else sci_name.split()[0]
            n = alias_counter.get(prefix, 0) + 1
            alias_counter[prefix] = n
            alias = f"{prefix} {n}" if rank == "morphospecies" else sci_name

            t = Taxon(
                project_id=proj.id,
                parent_taxon_id=parent_id,
                scientific_name=sci_name,
                rank=rank,
                common_name=common,
                alias=alias,
            )
            db.add(t)
            db.flush()
            taxon_map[sci_name] = t

        # Sampling events + replicates + records
        terminal_locs = ["Punto N1", "Punto N2", "Punto S1"]
        record_data = [
            # (taxon, count per replicate list)
            ("Chrysomela populi", [5, 3, 7]),
            ("Curculio glandium", [2, 4, 1]),
            ("Chrysomelidae sp. 1", [8, 5, 3]),
            ("Chrysomelidae sp. 2", [1, 0, 4]),
            ("Baetis sp. 1", [12, 9, 15]),
            ("Baetis sp. 2", [6, 4, 8]),
            ("Chironomus sp. 1", [20, 18, 22]),
        ]

        for loc_name in terminal_locs:
            loc = loc_map[loc_name]
            ev = SamplingEvent(
                project_id=proj.id,
                location_id=loc.id,
                start_date="2024-03-15",
                end_date="2024-03-15",
                description=f"Muestreo inicial en {loc_name}",
            )
            db.add(ev)
            db.flush()

            for rep_idx, rep_code in enumerate(["R1", "R2", "R3"]):
                method = method_map["RED"] if loc_name != "Punto S1" else method_map["SURBER"]
                rep = Replicate(event_id=ev.id, code=rep_code, method_id=method.id)
                db.add(rep)
                db.flush()

                for taxon_name, counts in record_data:
                    c = counts[rep_idx]
                    if c > 0:
                        rec = OccurrenceRecord(
                            replicate_id=rep.id,
                            taxon_id=taxon_map[taxon_name].id,
                            individual_count=c,
                            method_id=method.id,
                        )
                        db.add(rec)

        db.commit()
        print(f"Seed complete: project '{proj.name}' (id={proj.id})")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        if close_after:
            db.close()


if __name__ == "__main__":
    seed()
