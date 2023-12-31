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
        ose_input = {}

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
            Tlabel = f"{region}&{Tcode}&{outFcode}"
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
            Tlabel = f"{region}&{Tcode}&{outFcode}"
            Tlabels_conv.add(Tlabel)
        for f in conv_tech.in_fuels:
            inFcode = f.code
            Tlabel = f"{region}&{Tcode}&{inFcode}"
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
            Tlabel = f"{region}&DEM{Tcode}&{inFcode}"
            Tlabels_dem.add(Tlabel)

        return Tlabels_dem

    def get_tech_fuel_fields(
            self, techs: list[reslac.Technology]
    ) -> list[str]:
        """Label as <REG>&<TEC>&<FUE>.

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

    def __set_region(self, set_fields: list) -> list:
        """Define SET: REGION.

        Split and label as: <REG>.
        """
        regions = list({r.split("&")[0] for r in set_fields})
        regions.sort()
        return regions

    def __set_fuel(self, set_fields: list) -> list:
        """Define SET: FUEL.

        Split and label as: <REG><FUE>.
        """
        fuels = set()
        for fiels in set_fields:
            r_code, _, f_code = fiels.split("&")
            fuel_label = f"{r_code}{f_code}"
            fuels.add(fuel_label)

        fuels = list(fuels)
        fuels.sort()
        return fuels

    def __set_technology(self, set_fields: list) -> list:
        """Define SET: TECHNOLOGY.

        Split and label as: <REG><TEC><FUE>.
        """
        techs = set()
        for fiels in set_fields:
            r_code, t_code, f_code = fiels.split("&")
            tech_label = f"{r_code}{t_code}{f_code}"
            techs.add(tech_label)

        techs = list(techs)
        techs.sort()
        return techs

    def set_sets(
            self,
            res: reslac.EnergyMatrix,
    ) -> tuple[list]:
        """Call private methods of each SET.

        Define SETS (indices) of the model.

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
        set_fields = self.get_tech_fuel_fields(techs)
        region_col = self.__set_region(set_fields=set_fields)
        tech_col = self.__set_technology(set_fields=set_fields)
        fuel_col = self.__set_fuel(set_fields=set_fields)
        return (region_col, tech_col, fuel_col)

    def dem_tech_energy(
            self,
            dem_tech: reslac.Demand_Tech
    ) -> list[tuple]:
        """Get energy of demanded fuel.

        Similar to :py:meth:`oseinput.__label_dem_tech`.
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

        Note: Names longer than **31** characters require a
        ``short_name`` field.
        This is due to character limits on excel sheet names.
        ``otoole`` will raise an error if a ``short_name``
        is not provided in these instances.

        Long ``parameter`` type with short_name
        ---------------------------------------

        TotalAnnualMaxCapacityInvestment:
            short_name: TotalAnnualMaxCapacityInvestmen

        TotalAnnualMinCapacityInvestment:
            short_name: TotalAnnualMinCapacityInvestmen

        TotalTechnologyAnnualActivityLowerLimit:
            short_name: TotalTechnologyAnnualActivityLo

        TotalTechnologyAnnualActivityUpperLimit:
            short_name: TotalTechnologyAnnualActivityUp

        TotalTechnologyModelPeriodActivityLowerLimit:
            short_name: TotalTechnologyModelPeriodActLo

        TotalTechnologyModelPeriodActivityUpperLimit:
            short_name: TotalTechnologyModelPeriodActUp

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
        ]

        Long ``result`` type with short_name
        ------------------------------------

        DiscountedTechnologyEmissionsPenalty:
            short_name: DiscountedTechEmissionsPenalty

        RateOfProductionByTechnologyByMode:
            short_name: RateOfProductionByTechByMode

        TotalAnnualTechnologyActivityByMode:
            short_name: TotalAnnualTechActivityByMode

        TotalTechnologyModelPeriodActivity:
            short_name: TotalTechModelPeriodActivity

        Note: ``result`` type are missing in the OSeInputData.xlsx but
        not in ``config.yaml``. Moreover, When referencing set indices
        in ``config.yaml``
        use the full name, not the ``short_name``.

        """
        accumulated_annual_demand = self.__accumulated_annual_demand(res=res)
        return (accumulated_annual_demand, )

    def write_excel_oseinput(self, data: dict) -> None:
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
        regions, tech_col, fuel_col, = self.set_sets(res=res)
        parameters = self.set_parameters(res=res)
        accumulated_annual_demand = parameters[0]

        # Populate
        # --------
        # SETS
        ose_data["TECHNOLOGY"]["VALUE"] = tech_col
        ose_data["FUEL"]["VALUE"] = fuel_col
        ose_data["REGION"]["VALUE"] = regions
        # PATAMETERS
        sheet01 = "AccumulatedAnnualDemand"
        ose_data[sheet01]["REGION"] = accumulated_annual_demand["Region"]
        ose_data[sheet01]["FUEL"] = accumulated_annual_demand["Label"]
        ose_data[sheet01][2021] = accumulated_annual_demand["Energy_PJ"]
        ose_data[sheet01][2021] = abs(ose_data[sheet01][2021])

        # Generate file
        # -------------
        self.write_excel_oseinput(data=ose_data)
        return ose_data


if __name__ == "__main__":
    input_data = Input_Data()
    ose_input = input_data.fill_structure()
