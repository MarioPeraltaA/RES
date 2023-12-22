"""Setup RES from the Energetic Matrix Balance.

This module setup the technologies and fuels attributes
and values availables in the Energetic Matrix Balance
of any country following the OSeMOSYS naming convention.

Note: According to the naming convention used by OSeMOSYS
a 3-letter country abbreviation will be adopted in front
of the code (label) as follows:

    [region][category][sector][fuel/commodity][###]

e.g. for "Crude oil extraction" kind of technology in
"Argentina" the generic convention label is: ``ARGPROCRU``
This module also takes into account the Capacity matrix
of any country.

Author: Mario R. Peralta. A.
email: Mario.Peralta@ucr.ac.cr
The Electric Power and Energy Research Laboratory (EPERLab).

"""
import pandas as pd
import copy


class Technology():

    def __init__(self,
                 code: str,
                 region: str,
                 category: str):
        self.code = code
        self.region = region
        self.category = category

    def __repr__(self) -> str:
        r = self.region
        c = self.code
        cat = self.category
        return f"({cat}, {c}, {r})"

    def __eq__(self, other) -> bool:
        m_type = type(self)
        n_type = type(other)
        m_cat = self.category
        n_cat = other.category
        m_c = self.code
        n_c = other.code
        m_r = self.region
        n_r = other.region
        self_ft = {m_type, m_cat, m_c, m_r}
        other_ft = {n_type, n_cat, n_c, n_r}

        return self_ft == other_ft

    def __add__(self, other):
        """LOSTEC: LOS001, LOS002.

        """
        if type(self) == type(other):
            # Operate
            s_code = self.code
            o_code = other.code
            tech_set = {s_code, o_code}
            # Primary loss tech
            if tech_set == {"INV", "WAS"}:
                for f in self.out_fuels:
                    energy = other.out_fuels[
                        other.out_fuels.index(f)
                    ].energy_PJ
                    f.energy_PJ += energy
                return self

            # Demand loss tech
            elif tech_set == {"OWN", "LOS"}:
                for f in self.in_fuels:
                    energy = other.in_fuels[
                        other.in_fuels.index(f)
                    ].energy_PJ
                    f.energy_PJ += energy
                return self

            else:
                print("LOSTEC: LOS001 or LOS002 only.")
                return None

        else:
            print(f"TypeError: Different categories")
            return None


class Primary_Tech(Technology):

    def __init__(self,
                 label: str,
                 region: str,
                 category: str):
        super().__init__(label, region, category)
        self.out_fuels = []


class Supply_Tech(Technology):

    def __init__(self,
                 label: str,
                 region: str,
                 category: str,
                 order: int):
        super().__init__(label, region, category)
        self.in_fuels = []
        self.out_fuels = []
        self.order = order


class Convertion_Tech(Technology):

    def __init__(self,
                 label: str,
                 region: str,
                 category: str):
        super().__init__(label, region, category)
        self.in_fuels = []
        self.out_fuels = []


class Demand_Tech(Technology):

    def __init__(self,
                 label: str,
                 region: str,
                 category: str):
        super().__init__(label, region, category)
        self.in_fuels = []


class Fuel():

    def __init__(
            self, code: str,
            energy: float, region: str
    ):
        self.code = code
        self.energy_PJ = energy
        self.region = region

    def __repr__(self) -> str:
        c = self.code
        r = self.region
        return f"({c}, {r})"

    def __eq__(self, other) -> bool:
        m_type = type(self)
        n_type = type(other)
        m_c = self.code
        n_c = other.code
        m_r = self.region
        n_r = other.region
        self_ft = {m_type, m_c, m_r}
        other_ft = {n_type, n_c, n_r}
        return self_ft == other_ft

class Primary_Fuel(Fuel):

    def __init__(self, code: str, energy: float, region: str):
        super().__init__(code, energy, region)


class Second_Fuel(Fuel):

    def __init__(self, code: str, energy: float, region: str):
        super().__init__(code, energy, region)


class Third_Fuel(Fuel):

    def __init__(self, code: str, energy: float, region: str):
        super().__init__(code, energy, region)


class Supply_Fuel(Fuel):

    def __init__(self,
                 order: int,
                 code: str,
                 energy: float, region: str):
        super().__init__(code, energy, region)
        self.order = order


class EnergyMatrix():

    def __init__(self):
        self.matrix = {}    # Balance matrix
        self.res = {}       # Merge capacities & balance
        self.techs = []
        self.fuels = []
        self.labels = []    # To instance capacities fuels
        self._techs = []    # Intances to be updated
        self._fuels = []    # Intances to be updated

    def read_data(self, path: str = "./data/matrix.xlsx") -> dict:
        """Read Energetic Balance Matrix data.

        It gives string format to commodities (fields)
        and sectors (register).

        """
        dict_df = pd.read_excel(path, sheet_name=None, header=4)
        # Set new columns header
        for matrix_df in dict_df.values():
            # Replace empty values in fields by "Sectors"
            matrix_df.rename(columns={"Unnamed: 0": "Sectors"}, inplace=True)
            # In register by "Unit"
            matrix_df["Sectors"] = matrix_df["Sectors"].fillna("Unit")
            # Remove white space in field
            matrix_df.columns = matrix_df.columns.str.strip()
            # Remove white space in register
            matrix_df["Sectors"] = matrix_df["Sectors"].str.strip()
            # Replace all np.NaN obj for 0.0 float type
            matrix_df.fillna(0.0, inplace=True)

        self.matrix = dict_df
        return dict_df

    def read_base(self,
                  path: str = "./data/capacities.xlsx") -> dict:
        """Read Capacities Matrix data.

        It reads binary matrix:
            - ``1`` there is a likelihood the technology
              could describe the energy system under certain scenario.
            - ``0`` No chance whatsoever to somehow describe
              the energy system because of technical incompatibility.

        """
        dict_df = pd.read_excel(path, sheet_name=None, header=4)
        # Set new columns header
        for matrix_df in dict_df.values():
            # Replace empty values in fields by "Sectors"
            matrix_df.rename(columns={"Unnamed: 0": "Sectors"}, inplace=True)
            # In register by "Unit"
            matrix_df["Sectors"] = matrix_df["Sectors"].fillna("Unit")
            # Remove white space in field
            matrix_df.columns = matrix_df.columns.str.strip()
            # Remove white space in register
            matrix_df["Sectors"] = matrix_df["Sectors"].str.strip()
            # Replace all np.NaN obj for 0.0 float type
            matrix_df.fillna(0.0, inplace=True)

        self.res = dict_df
        return dict_df

    def add_prim_tech(self,
                      label,
                      region,
                      category) -> Primary_Tech:
        prim_tech = Primary_Tech(label, region, category)
        # Update system
        self.techs.append(prim_tech)
        return prim_tech

    def add_conv_tech(self,
                      label,
                      region,
                      category) -> Convertion_Tech:
        conv_tech = Convertion_Tech(label, region, category)
        self.techs.append(conv_tech)
        return conv_tech

    def add_demand_tech(self,
                        label,
                        region,
                        category) -> Demand_Tech:
        demand_tech = Demand_Tech(label, region, category)
        self.techs.append(demand_tech)
        return demand_tech

    def set_prim_tech(self,
                      tech_code,
                      region,
                      category,
                      matrix_df,
                      n) -> Primary_Tech:
        tech = self.add_prim_tech(tech_code, region, category)
        # Add all output primary fuels to this same instance
        for field in matrix_df.columns:
            fuelID = set_fuel_labels(field)
            if not fuelID:
                continue
            sector, fuel_code = fuelID
            if tech_code == "PRO" and sector in {"FUE002", "FUE003"}:
                continue
            energy = matrix_df[field][n]
            if tech_code in {"EXP", "WAS"}:
                energy = -energy    # Negative
            fuel = self.add_fuel(sector, fuel_code, energy, region)
            tech.out_fuels.append(fuel)

        return tech

    def set_conv_tech(self,
                      tech_code,
                      region,
                      category,
                      matrix_df,
                      n) -> Convertion_Tech:
        tech = self.add_conv_tech(tech_code, region, category)
        for field in matrix_df.columns:
            fuelID = set_fuel_labels(field)
            if not fuelID:
                continue
            sector, fuel_code = fuelID
            # Primary fuel as inputs only
            if category == "UPS001":
                if sector == "FUE003":
                    continue
                energy = matrix_df[field][n]
                fuel = self.add_fuel(sector, fuel_code, energy, region)
                # Input
                if sector == "FUE001":
                    tech.in_fuels.append(fuel)
                # Output
                elif sector == "FUE002":
                    tech.out_fuels.append(fuel)

            elif category == "UPS002":
                if sector == "FUE003":
                    continue
                energy = matrix_df[field][n]
                fuel = self.add_fuel(sector, fuel_code, energy, region)
                tech.in_fuels.append(fuel)
                if sector == "FUE002":
                    fuel = copy.deepcopy(fuel)
                    tech.out_fuels.append(fuel)

            elif category == "UPS003":
                energy = matrix_df[field][n]
                fuel = self.add_fuel(sector, fuel_code, energy, region)
                if sector == "FUE003":
                    tech.out_fuels.append(fuel)
                else:
                    tech.in_fuels.append(fuel)

        return tech

    def set_demand_tech(self,
                        tech_code,
                        region,
                        category,
                        matrix_df,
                        n) -> Demand_Tech:
        tech = self.add_demand_tech(tech_code, region, category)
        for field in matrix_df.columns:
            fuelID = set_fuel_labels(field)
            if not fuelID:
                continue
            sector, fuel_code = fuelID
            energy = -matrix_df[field][n]   # Negative as input
            fuel = self.add_fuel(sector, fuel_code, energy, region)
            tech.in_fuels.append(fuel)

        return tech

    def add_tech(self,
                 tech_code: str,
                 region: str,
                 category: str,
                 matrix_df: pd.DataFrame,
                 n: int) -> Technology:
        """Creat and add technology instance.
 
        """
        # Primary tech
        if category in {"SUP", "LOS001"}:
            tech = self.set_prim_tech(tech_code,
                                      region,
                                      category,
                                      matrix_df,
                                      n)

        # Convertion tech
        elif category in {"UPS001", "UPS002", "UPS003"}:
            tech = self.set_conv_tech(tech_code,
                                      region,
                                      category,
                                      matrix_df,
                                      n)


        # Demand tech
        elif category in {"DEM", "LOS002"}:
            tech = self.set_demand_tech(tech_code,
                                        region,
                                        category,
                                        matrix_df,
                                        n)
        return tech

    def add_prim_fuel(self, code, energy, region) -> Primary_Fuel:
        prim_fuel = Primary_Fuel(code, energy, region)
        self.fuels.append(prim_fuel)
        return prim_fuel

    def add_sec_fuel(self, code, energy, region) -> Second_Fuel:
        sec_fuel =  Second_Fuel(code, energy, region)
        self.fuels.append(sec_fuel)
        return sec_fuel

    def add_third_fuel(self, code, energy, region) -> Third_Fuel:
        third_fuel = Third_Fuel(code, energy, region)
        self.fuels.append(third_fuel)
        return third_fuel

    def add_fuel(self,
                 sector: str,
                 fuel_code: str,
                 energy: float, region: str) -> Fuel:
        # Primary fuel
        if sector == "FUE001":
            fuel = self.add_prim_fuel(fuel_code, energy, region)
        # Second fuel
        elif sector == "FUE002":
            fuel = self.add_sec_fuel(fuel_code, energy, region)
        # Third fuel
        elif sector == "FUE003":
            fuel = self.add_third_fuel(fuel_code, energy, region)
        return fuel

    def add_supply_tech(self):
        pass

    def add_supply_fuel(self):
        pass

    def split_flow(self) -> None:
        """UPS002 input and output fuels.

        """
        techs = self.techs
        conv_techs = [t for t in techs if t.category == "UPS002"]
        for c in conv_techs:
            for f in c.in_fuels:
                if f.energy_PJ > 0:
                    f.energy_PJ = 0
            for f in c.out_fuels:
                if f.energy_PJ < 0:
                    f.energy_PJ = 0

    def obj_labels(self) -> list[tuple[str]]:
        """Set objects labels to be instanced.

        """
        dict_df = self.read_base()
        # Iterate over data
        for country, matrix_df in dict_df.items():
            region = country.split(" - ")[1]
            region = set_region(region)
            sectors = matrix_df["Sectors"]
            for n, tech in enumerate(sectors):
                techID = set_technology_labels(tech)
                if not techID:
                    continue
                category, tech_code = techID
                for field in matrix_df.columns:
                    fuelID = set_fuel_labels(field)
                    if fuelID:
                        sector, fuel_code = fuelID
                        energy = matrix_df[field][n]
                        if energy:
                            fuel_str = (category,
                                        tech_code,
                                        sector,
                                        fuel_code,
                                        region)
                            self.labels.append(fuel_str)

        return self.labels

    def add_ifuel(self, sector, fuel_code, region) -> Fuel:
        """Initial fuels.

        """
        energy = 0   # Initial value
        if sector == "FUE001":
            fuel = Primary_Fuel(fuel_code, energy, region)
        elif sector == "FUE002":
            fuel = Second_Fuel(fuel_code, energy, region)
        elif sector == "FUE003":
            fuel = Third_Fuel(fuel_code, energy, region)

        self._fuels.append(fuel)
        return fuel

    def add_itech(self,
                  category,
                  tech_code,
                  region) -> Technology:
        # Primary tech
        if category in {"SUP", "LOS001"}:
            tech = Primary_Tech(tech_code, region, category)
        # Convertion tech
        elif category in {"UPS001", "UPS002", "UPS003"}:
            tech = Convertion_Tech(tech_code, region, category)
        # Demand tech
        elif category in {"DEM", "LOS002"}:
            tech = Demand_Tech(tech_code, region, category)

        self._techs.append(tech)
        return tech

    def prim_tech_flow(self,
                       tech: Technology,
                       obj_labels: list[tuple[str]]) -> Primary_Tech:
        # Output
        tech_code = tech.code
        region = tech.region
        filter = {tech_code,
                  region,
                  "FUE001",
                  "FUE002",
                  "FUE003"}
        out_fuels = list({ft for ft in obj_labels
                         if {ft[1], ft[2], ft[-1]}.issubset(filter)})
        out_fuels = [self.add_ifuel(s, f, r)
                     for _, _, s, f, r in out_fuels]
        tech.out_fuels = out_fuels

        return tech

    def conv_tech_flow(self,
                       tech: Technology,
                       obj_labels: list[tuple[str]]) -> Convertion_Tech:
        category = tech.category
        tech_code = tech.code
        region = tech.region

        if category == "UPS001":
            # Input
            in_filter = {tech_code, "FUE001", region}
            in_fuels = list({ft for ft in obj_labels
                             if {ft[1], ft[2], ft[-1]}.issubset(in_filter)})
            in_fuels = [self.add_ifuel(s, f, r)
                        for _, _, s, f, r in in_fuels]
            tech.in_fuels = in_fuels
            # Output
            out_filter = {tech_code, "FUE002", region}
            out_fuels = list({ft for ft in obj_labels
                              if {ft[1], ft[2], ft[-1]}.issubset(out_filter)})
            out_fuels = [self.add_ifuel(s, f, r)
                         for _, _, s, f, r in out_fuels]
            tech.out_fuels = out_fuels

        elif category == "UPS002":
            # Input: for negative values of FUE002
            in_filter = {tech_code, "FUE001", "FUE002", region}
            in_fuels = list({ft for ft in obj_labels
                          if {ft[1], ft[2], ft[-1]}.issubset(in_filter)})
            in_fuels = [self.add_ifuel(s, f, r)
                        for _, _, s, f, r in in_fuels]
            tech.in_fuels = in_fuels
            # Output: for positive values of FUE002
            out_filter = {tech_code, "FUE002", region}
            out_fuels = list({ft for ft in obj_labels
                          if {ft[1], ft[2], ft[-1]}.issubset(out_filter)})
            out_fuels = [self.add_ifuel(s, f, r)
                         for _, _, s, f, r in out_fuels]
            tech.out_fuels = out_fuels

        elif category == "UPS003":
            # Input
            in_filter = {tech_code, "FUE001", "FUE002", region}
            in_fuels = list({ft for ft in obj_labels
                             if {ft[1], ft[2], ft[-1]}.issubset(in_filter)})
            in_fuels = [self.add_ifuel(s, f, r)
                        for _, _, s, f, r in in_fuels]
            tech.in_fuels = in_fuels
            # Output
            out_filter = {tech_code, "FUE003", region}
            out_fuels = list({ft for ft in obj_labels
                              if {ft[1], ft[2], ft[-1]}.issubset(out_filter)})
            out_fuels = [self.add_ifuel(s, f, r)
                         for _, _, s, f, r in out_fuels]
            tech.out_fuels = out_fuels

        return tech

    def dem_tech_flow(self,
                      tech: Technology,
                      obj_labels: list[tuple[str]]) -> Demand_Tech:

        # Income only
        tech_code = tech.code
        region = tech.region
        in_filter = {tech_code,
                     "FUE001",
                     "FUE002",
                     "FUE003",
                     region}
        in_fuels = list({ft for ft in obj_labels
                     if {ft[1], ft[2], ft[-1]}.issubset(in_filter)})
        in_fuels = [self.add_ifuel(s, f, r)
                    for _, _, s, f, r in in_fuels]
        tech.in_fuels = in_fuels
        return tech

    def initital_RES(self) -> list[Technology]:
        """Instances.

        Initial RES with space in memory for those
        technology that has some capacities to describe
        somehow the energy system.
        It initializes fuel flows in zero.

        """
        obj_labels = self.obj_labels()
        # Filter techs
        techs = list({(ft[0], ft[1], ft[-1]) for ft in obj_labels})
        # Add techs
        for category, tech_code, region in techs:
            tech = self.add_itech(category, tech_code, region)
            # Add initial fuels
            if category in {"SUP", "LOS001"}:
                tech = self.prim_tech_flow(tech, obj_labels)
            elif category in {"UPS001", "UPS002", "UPS003"}:
                tech = self.conv_tech_flow(tech, obj_labels)
            elif category in {"DEM", "LOS002"}:
                tech = self.dem_tech_flow(tech, obj_labels)

        return self._techs

    def data_RES(self) -> list[Technology]:
        """It intances all possible fuels.

        It reads throughout the Energetic
        Balance Matrix data.

        """
        dict_df = self.read_data()
        # Iterate over data
        for country, matrix_df in dict_df.items():
            region = country.split(" - ")[1]
            region = set_region(region)
            sectors = matrix_df["Sectors"]
            for n, tech in enumerate(sectors):
                techID = set_technology_labels(tech)
                if not techID:
                    continue
                category, tech_code = techID
                tech = self.add_tech(tech_code,
                                     region,
                                     category,
                                     matrix_df,
                                     n)
        # UPS002 flow
        self.split_flow()
        return self.techs

    def fill_RES(self) -> list[Technology]:
        """Update energy flow attributes.

        It sets the actual values of flowing fuels
        per country. Merge.

        """
        itechs = self.initital_RES()
        techs = self.data_RES()
        for T in itechs:
            t = techs[techs.index(T)]
            if T.category in {"SUP", "LOS001"}:
                for f in T.out_fuels:
                    out_fuel = t.out_fuels[t.out_fuels.index(f)]
                    f.energy_PJ = out_fuel.energy_PJ

            elif T.category in {"UPS001", "UPS002", "UPS003"}:
                for f in T.in_fuels:
                    in_fuel = t.in_fuels[t.in_fuels.index(f)]
                    f.energy_PJ = in_fuel.energy_PJ

                for f in T.out_fuels:
                    out_fuel = t.out_fuels[t.out_fuels.index(f)]
                    f.energy_PJ = out_fuel.energy_PJ

            elif T.category in {"DEM", "LOS002"}:
                for f in T.in_fuels:
                    in_fuel = t.in_fuels[t.in_fuels.index(f)]
                    f.energy_PJ = in_fuel.energy_PJ

        return itechs

    def sum_prim_loss_tech(self, techs: list) -> None:
        # Filter regions
        regions = list({T.region for T in techs})
        # Operate WAS & INV techs for each region
        for r in regions:
            was_tech = [T for T in techs
                        if all((T.code=="WAS", T.region==r))][0]
            inv_tech = [T for T in techs
                        if all((T.code=="INV", T.region==r))][0]
            # Operate
            _ = was_tech + inv_tech
            # Remove INV tech
            self._techs.remove(inv_tech)

    def sum_sec_loss_tech(self, techs: list) -> None:
        # Filter regions
        regions = list({T.region for T in techs})
        # Operate OWN & LOS techs for each region
        for r in regions:
            own_tech = [T for T in techs
                        if all((T.code=="OWN", T.region==r))][0]
            los_tech = [T for T in techs
                        if all((T.code=="LOS", T.region==r))][0]
            # Operate: Update OWN
            _ = own_tech + los_tech
            # Remove LOS tech
            self._techs.remove(los_tech)

    def build_RES(self) -> list[Technology]:
        """Reduce RES.

        """
        techs = self.fill_RES()
        self.sum_prim_loss_tech(techs)
        self.sum_sec_loss_tech(techs)

        return self._techs


def set_region(country: str) -> str:
    """Set regions name up.

    Region
    ------
    regions = {
        "Argentina": "ARG",
        "Barbados": "BRB",
        "Belice": "BLZ",
        "Bolivia": "BOL",
        "Brasil": "BRA",
        "Chile": "CHL",
        "Colombia": "COL",
        "Costa Rica": "CRI",
        "Cuba": "CUB",
        "Ecuador": "ECU",
        "El Salvador": "SLV",
        "Grenada": "GRD",
        "Guatemala": "GTM",
        "Guyana": "GUY",
        "Haiti": "HTI",
        "Honduras": "HND",
        "Jamaica": "JAM",
        "México": "MEX",
        "Nicaragua": "NIC",
        "Panamá": "PAN",
        "Paraguay": "PRY",
        "Perú": "PER",
        "República Dominicana": "DOM",
        "Suriname": "SUR",
        "Trinidad & Tobago": "TTO",
        "Uruguay": "URY",
        "Venezuela": "VEN"
    }

    """
    region = {
        "Argentina": "ARG",
        "Barbados": "BRB",
        "Belice": "BLZ",
        "Bolivia": "BOL",
        "Brasil": "BRA",
        "Chile": "CHL",
        "Colombia": "COL",
        "Costa Rica": "CRI",
        "Cuba": "CUB",
        "Ecuador": "ECU",
        "El Salvador": "SLV",
        "Grenada": "GRD",
        "Guatemala": "GTM",
        "Guyana": "GUY",
        "Haiti": "HTI",
        "Honduras": "HND",
        "Jamaica": "JAM",
        "México": "MEX",
        "Nicaragua": "NIC",
        "Panamá": "PAN",
        "Paraguay": "PRY",
        "Perú": "PER",
        "República Dominicana": "DOM",
        "Suriname": "SUR",
        "Trinidad & Tobago": "TTO",
        "Uruguay": "URY",
        "Venezuela": "VEN"
    }
    if country in region:
        return region[country]
    else:
        return False


def set_fuel_labels(name: str) -> tuple:
    """Set OSeMOSYS commodity naming convention.

    It replaces the name of commodity for three-letter label
    so that the OSeMOSYS code naming can be set up.

    """
    # Fuels
    # -----
    prim_fuel_labels = {
        "Sector": "FUE001",
        "PETRÓLEO": "CRU",
        "GAS NATURAL": "NGS",
        "CARBÓN MINERAL": "COA001",
        "HIDROENERGÍA": "HYD",
        "GEOTERMIA": "GEO",
        "NUCLEAR": "NUC",
        "LEÑA": "WOO",
        "CAÑA DE AZÚCAR Y DERIVADOS": "SGC",
        "OTRAS PRIMARIAS": "OPR"
    }
    sec_fuel_labels = {
        "Sector": "FUE002",
        "GAS LICUADO DE PETRÓLEO": "LPG",
        "GASOLINA/ALCOHOL": "GSL",
        "KEROSENE/JET FUEL": "KER",
        "DIÉSEL OIL": "DSL",
        "FUEL OIL": "HFO",
        "COQUE": "COK",
        "CARBÓN VEGETAL": "COA002",
        "GASES": "GAS",
        "OTRAS SECUNDARIAS": "OSE",
        "NO ENERGÉTICO": "NEN"
    }
    third_fuel_labels = {
        "Sector": "FUE003",
        "ELECTRICIDAD": "ELC"
    }

    commodities = [prim_fuel_labels,
                   sec_fuel_labels,
                   third_fuel_labels]
    for c in commodities:
        if name in c:
            return (c["Sector"], c[name])
        else:
            continue
    return False


def set_technology_labels(name: str) -> str:
    """Set OSeMOSYS technology naming convention.

    It replaces the name of sector or technology
    for three-letter label so that the OSeMOSYS
    code naming can be set up.

    Note: Final demand category would not be considered since is
    the sum of Energetic and Non-energetic demand.

    Note: These losses sectors will be considere the same
    sort of :py:class:`Primary_Tech` technology whose:

    {
        "VARIACIÓN DE INVENTARIOS",
        "NO APROVECHADO",
        "PÉRDIDAS",
        "CONSUMO PROPIO"
    }
    whose category will be ``LOS`` that stands for loss.

    """
    # Supply category
    # ---------------
    supply = {
        "Category": "SUP",
        "PRODUCCIÓN": "PRO",
        "IMPORTACIÓN": "IMP",
        "EXPORTACIÓN": "EXP"
    }

    # Transformation
    # --------------
    # Conversion technology
    sec_tech = {
        "Category": "UPS001",
        "REFINERÍAS": "REF",
        "CENTROS DE GAS": "GAS",
        "CARBONERA": "CHL",
        "DESTILERÍA": "DET"
    }
    third_tech = {
        "Category": "UPS002",
        "COQUERÍA Y ALTOS HORNOS": "BOI",
        "OTROS CENTROS": "UPSTEC"
    }
    fourth_tech = {
        "Category": "UPS003",
        "CENTRALES ELÉCTRICAS": "PWR",
        "AUTOPRODUCTORES": "SEL"
    }
    # Energy demand category
    # ----------------------
    demand = {
        "Category": "DEM",
        "TRANSPORTE": "TRA",
        "INDUSTRIAL": "IND",
        "RESIDENCIAL": "RES",
        "COMERCIAL, SERVICIOS, PÚBLICO": "COM",
        "AGRO, PESCA Y MINERÍA": "AGR",
        "CONSTRUCCIÓN Y OTROS": "CON",
        "CONSUMO NO ENERGÉTICO": "NEE"
    }

    # Loss technology
    # ----------------
    loss_tech01 = {
        "Category": "LOS001",
        "VARIACIÓN DE INVENTARIOS": "INV",
        "NO APROVECHADO": "WAS",
    }

    loss_tech02 = {
        "Category": "LOS002",
        "PÉRDIDAS": "LOS",
        "CONSUMO PROPIO": "OWN"
    }

    categories = [
        supply,
        sec_tech,
        third_tech,
        fourth_tech,
        demand,
        loss_tech01,
        loss_tech02
    ]

    for c in categories:
        if name in c:
            return (c["Category"], c[name])
        else:
            continue
    return False


if __name__ == "__main__":
    pass
