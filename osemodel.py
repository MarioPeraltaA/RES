"""Processor OSeMOSYS Data Input.

This module processes and structures the RES Sets
and Parameters to ensure accurate data input and
seamless integration into the OSeMOSYS platform.

Author: Mario R. Peralta A.
email: Mario.Peralta@ucr.ac.cr
The Electric Power and Energy Research Laboratory (EPERLab).

"""
import reslac
import pandas as pd


class Input_Data():

    def __init__(self):
        ose_model = {}

    def call_reslac(self) -> reslac.EnergyMatrix:
        matrix = reslac.EnergyMatrix()
        _ = matrix.build_RES()
        self.res = matrix
        return matrix

    def call_template(
            self,
            file_path: str = "./template/template.xlsx"
    ) -> dict[pd.DataFrame]:
        ose_data = pd.read_excel(
            file_path,
            sheet_name=None
        )
        return ose_data

    def __label_prim_tech(
            self,
            prim_tech: reslac.Primary_Tech
    ) -> set:
        """Unpack & concat codes of primary technology."""
        Tlabels_prim = set()
        region = prim_tech.region
        Tcode = prim_tech.code
        for f in prim_tech.out_fuels:
            outFcode = f.code
            Tlabel = f"{region}&{Tcode}{outFcode}"
            Tlabels_prim.add(Tlabel)

        return Tlabels_prim

    def __label_conv_tech(
            self,
            conv_tech: reslac.Convertion_Tech
    ) -> set:
        """Unpack & concat codes of convertion technology."""
        Tlabels_conv = set()
        region = conv_tech.region
        Tcode = conv_tech.code
        for f in conv_tech.out_fuels:
            outFcode = f.code
            Tlabel = f"{region}&{Tcode}{outFcode}"
            Tlabels_conv.add(Tlabel)
        for f in conv_tech.in_fuels:
            inFcode = f.code
            Tlabel = f"{region}&{Tcode}{inFcode}"
            Tlabels_conv.add(Tlabel)

        return Tlabels_conv

    def __label_dem_tech(
            self,
            dem_tech: reslac.Demand_Tech
    ) -> set:
        """Unpack & concat codes of demand technology."""
        Tlabels_dem = set()
        region = dem_tech.region
        Tcode = dem_tech.code
        for f in dem_tech.in_fuels:
            inFcode = f.code
            # Add "DEM" code
            Tlabel = f"{region}&DEM{Tcode}{inFcode}"
            Tlabels_dem.add(Tlabel)

        return Tlabels_dem

    def get_tech_labels(
            self, techs: list[reslac.Technology]
    ) -> list[str]:
        """Label as <REG>&<TEC><FUE>.

        It distributes (unpacks) the technology code to each
        output or input fuel code to generate the
        technology complete label in the following format:

            <REG>&<TEC><FUE>

        Where each code stands for:

            - REG: Region
            - TEC: Technology
            - FUE: Fuel

        According to OSeMOSYS three letters naming convention.
        """
        Tlabels_prim = set()
        Tlabels_conv = set()
        Tlabels_dem = set()
        for T in techs:
            if isinstance(T, reslac.Primary_Tech):
                prim_techs = self.__label_prim_tech(prim_tech=T)
                Tlabels_prim = Tlabels_prim.union(prim_techs)
            elif isinstance(T, reslac.Convertion_Tech):
                conv_techs = self.__label_conv_tech(conv_tech=T)
                Tlabels_conv = Tlabels_conv.union(conv_techs)
            elif isinstance(T, reslac.Demand_Tech):
                dem_techs = self.__label_dem_tech(dem_tech=T)
                Tlabels_dem = Tlabels_dem.union(dem_techs)

        # To list
        Tlabels_prim = list(Tlabels_prim)
        Tlabels_conv = list(Tlabels_conv)
        Tlabels_dem = list(Tlabels_dem)
        # Sort techs:
        Tlabels = Tlabels_prim + Tlabels_conv + Tlabels_dem
        return Tlabels

    def get_fuel_labels(
            self, fuels: list
    ) -> list[str]:
        """Label as <REG><FUE>.

        Similar as :py:meth:`osemodel.get_tech_labels`
        it generates the labels for each fuel
        of the LAC system.

        """
        pass

    def set_sets(
            self,
            res: reslac.EnergyMatrix
    ) -> tuple[list]:
        """Define SETS of the model.

        sets = [
            "YEAR",
            "TECHNOLOGY",
            "TIMESLICE",
            "FUEL",
            "EMISSION",
            "MODE_OF_OPERATION",
            "REGION",
            "SEASON",
            "DAYTYPE",
            "DAILYTIMEBRACKET",
            "STORAGE"
        ].
        """
        techs = res._techs
        fuels = res._fuels
        Tlabels = self.get_tech_labels(techs)
        regions = list({T.region for T in techs})
        regions.sort()
        Tcodes = []
        Fcodes = []
        # Sort by region
        for r in regions:
            f = [f"{r}{F.code}" for F in fuels if F.region == r]
            t = [T.replace("&", "") for T in Tlabels if r in T]
            Tcodes += t
            Fcodes += f

        return (Tcodes, Fcodes, regions)

    def dem_tech_energy(
            self,
            dem_tech: reslac.Demand_Tech
    ) -> list[tuple]:
        """Get energy of demanded fuel.

        Similar to :py:meth:`osemodel.__label_dem_tech`.
        Income energy amount of technology the demands fuel.
        """
        dem_fields = []
        region = dem_tech.region
        Tcode = dem_tech.code
        for f in dem_tech.in_fuels:
            inFcode = f.code
            Tlabel = f"{region}&DEM{Tcode}{inFcode}"
            dem_fields.append((Tlabel, f.energy_PJ))

        return dem_fields

    def split_label_energy_fields(
            self,
            label_parameters: list
    ) -> tuple[list]:
        """Unpack columns: REGION & LABEL & ENERGY."""
        regions = []
        dem_tech_labels = []
        energies = []
        for label, energy in label_parameters:
            region, dem_label = label.split("&")
            regions.append(region)
            dem_tech_labels.append(dem_label)
            energies.append(energy)

        return regions, dem_tech_labels, energies

    def __accumulated_annual_demand(
            self,
            res: reslac.EnergyMatrix
    ) -> dict:
        """Define parameter: AccumulatedAnnualDemand.

        Fields (keys): Region, Label, Energy_PJ.
        """
        techs = res._techs
        # Filter demand technology
        dem_techs = [T for T in techs
                     if isinstance(T, reslac.Demand_Tech)]
        regions = list({D.region for D in dem_techs})
        regions.sort()
        dem_tech_code = []
        for r in regions:
            dem_techs_r = [D for D in dem_techs if D.region == r]
            for D in dem_techs_r:
                dem_tech_code += self.dem_tech_energy(
                    dem_tech=D
                )

        demand_codes = {}
        cols = self.split_label_energy_fields(dem_tech_code)
        demand_codes["Region"] = cols[0]
        demand_codes["Label"] = cols[1]
        demand_codes["Energy_PJ"] = cols[2]
        return demand_codes

    def set_parameters(
            self, res: reslac.EnergyMatrix
    ) -> tuple[dict]:
        """Call private methods of each parameter.

        parameters = [
            'AccumulatedAnnualDemand', 'AnnualEmissionLimit',
            'AnnualExogenousEmission', 'AvailabilityFactor',
            'CapacityFactor', 'CapacityOfOneTechnologyUnit',
            'CapacityToActivityUnit', 'CapitalCost',
            'CapitalCostStorage',
            'Conversionld', 'Conversionlh',
            'Conversionls', 'DaySplit',
            'DaysInDayType', 'DepreciationMethod',
            'DiscountRate',
            'DiscountRateStorage', 'EmissionActivityRatio',
            'EmissionsPenalty',
            'FixedCost', 'InputActivityRatio', 'MinStorageCharge',
            'ModelPeriodEmissionLimit', 'ModelPeriodExogenousEmission',
            'OperationalLife', 'OperationalLifeStorage',
            'OutputActivityRatio',
            'REMinProductionTarget', 'RETagFuel',
            'RETagTechnology',
            'ReserveMargin', 'ReserveMarginTagFuel',
            'ReserveMarginTagTechnology',
            'ResidualCapacity',
            'ResidualStorageCapacity',
            'SpecifiedAnnualDemand', 'SpecifiedDemandProfile',
            'StorageLevelStart', 'StorageMaxChargeRate',
            'StorageMaxDischargeRate', 'TechnologyFromStorage',
            'TechnologyToStorage', 'TotalAnnualMaxCapacity',
            'TotalAnnualMaxCapacityInvestmen', 'TotalAnnualMinCapacity',
            'TotalAnnualMinCapacityInvestmen',
            'TotalTechnologyAnnualActivityLo',
            'TotalTechnologyAnnualActivityUp',
            'TotalTechnologyModelPeriodActLo',
            'TotalTechnologyModelPeriodActUp', 'TradeRoute',
            'VariableCost', 'YearSplit'
        ].
        """
        accumulated_annual_demand = self.__accumulated_annual_demand(res=res)
        return (accumulated_annual_demand, )

    def write_excel_osemodel(self, data: dict) -> None:
        """Osemosys structure.

        It generates a ``*.xlsx`` file with the
        SETS and PARAMETERS structure used by OSeMOSYS.

        """
        with pd.ExcelWriter(
            "./OSeInputData.xlsx"
        ) as writer:
            for sheet, df in data.items():
                df.to_excel(writer,
                            sheet_name=sheet,
                            index=False)

        return None

    def fill_structure(self):
        """Populate structure model template."""
        # Initialize
        # ---------
        res = self.call_reslac()
        ose_data = self.call_template()
        Tcode, Fcode, regions = self.set_sets(res=res)
        parameters = self.set_parameters(res=res)
        accumulated_annual_demand = parameters[0]

        # Populate
        # --------
        # SETS
        ose_data["TECHNOLOGY"]["VALUE"] = Tcode
        ose_data["FUEL"]["VALUE"] = Fcode
        ose_data["REGION"]["VALUE"] = regions
        # PATAMETERS
        sheet01 = "AccumulatedAnnualDemand"
        ose_data[sheet01]["REGION"] = accumulated_annual_demand["Region"]
        ose_data[sheet01]["FUEL"] = accumulated_annual_demand["Label"]
        ose_data[sheet01][2021] = accumulated_annual_demand["Energy_PJ"]
        ose_data[sheet01][2021] = abs(ose_data[sheet01][2021])

        # Generate file
        # -------------
        self.write_excel_osemodel(data=ose_data)
        return ose_data


if __name__ == "__main__":
    ose_model = Input_Data()
    ose_data = ose_model.fill_structure()
