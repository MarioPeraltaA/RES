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
        OSeModel = {}

    def call_resLAC(self) -> reslac.EnergyMatrix:
        matrix = reslac.EnergyMatrix()
        _ = matrix.build_RES()
        self.res = matrix
        return matrix

    def call_template(
            self,
            file_path: str = "./template/template.xlsx"
    ) -> dict[pd.DataFrame]:
        OSeData = pd.read_excel(
            file_path,
            sheet_name=None
        )
        return OSeData

    def get_techs_codes(
            self, techs: list[reslac.Technology]
    ) -> list[str]:
        """Labeled as <REG>&<TEC><FUE>.

        It distributes the technology code to each
        output or input fuel code to generate the
        technology complete label in the following format:

            <REG>&<TEC><FUE>

        Which stands for:

            - TEC: Technology
            - FUE: Fuel
            - REG: Region

        According to OSeMOSYS three letters naming convention.

        """
        Tlabels_prim = set()
        Tlabels_conv = set()
        Tlabels_dem = set()
        for T in techs:
            region = T.region
            Tcode = T.code
            if isinstance(T, reslac.Primary_Tech):
                for f in T.out_fuels:
                    outFcode = f.code
                    Tlabel = f"{region}&{Tcode}{outFcode}"
                    Tlabels_prim.add(Tlabel)
            elif isinstance(T, reslac.Convertion_Tech):
                for f in T.out_fuels:
                    outFcode = f.code
                    Tlabel = f"{region}&{Tcode}{outFcode}"
                    Tlabels_conv.add(Tlabel)
                for f in T.in_fuels:
                    inFcode = f.code
                    Tlabel = f"{region}&{Tcode}{inFcode}"
                    Tlabels_conv.add(Tlabel)
            elif isinstance(T, reslac.Demand_Tech):
                for f in T.in_fuels:
                    inFcode = f.code
                    Tlabel = f"{region}&{Tcode}{inFcode}"
                    Tlabels_dem.add(Tlabel)
        # To list
        Tlabels_prim = list(Tlabels_prim)
        Tlabels_conv = list(Tlabels_conv)
        Tlabels_dem = list(Tlabels_dem)
        # Sort techs:
        Tlabels = Tlabels_prim + Tlabels_conv + Tlabels_dem
        return Tlabels

    def get_fuels_codes(
            self, fuels: list
    ) -> list[str]:
        """Labeled as <REG><FUE>.

        Similar as :py:meth:`osemodel.get_techs_codes`
        it generates the labels for each fuel
        of the LAC system.

        """
        pass

    def set_sets(self):
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
        ]

        RES = self.call_resLAC()
        techs = RES._techs
        fuels = RES._fuels
        Tlabels = self.get_techs_codes(techs)
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

    def set_parameters(self):
        parameters = [
            'AccumulatedAnnualDemand', 'AnnualEmissionLimit',
            'AnnualExogenousEmission', 'AvailabilityFactor',
            'CapacityFactor', 'CapacityOfOneTechnologyUnit',
            'CapacityToActivityUnit', 'CapitalCost', 'CapitalCostStorage',
            'Conversionld', 'Conversionlh', 'Conversionls', 'DaySplit',
            'DaysInDayType', 'DepreciationMethod', 'DiscountRate',
            'DiscountRateStorage', 'EmissionActivityRatio', 'EmissionsPenalty',
            'FixedCost', 'InputActivityRatio', 'MinStorageCharge',
            'ModelPeriodEmissionLimit', 'ModelPeriodExogenousEmission',
            'OperationalLife', 'OperationalLifeStorage', 'OutputActivityRatio',
            'REMinProductionTarget', 'RETagFuel', 'RETagTechnology',
            'ReserveMargin', 'ReserveMarginTagFuel', 'ReserveMarginTagTechnology',
            'ResidualCapacity', 'ResidualStorageCapacity',
            'SpecifiedAnnualDemand', 'SpecifiedDemandProfile',
            'StorageLevelStart', 'StorageMaxChargeRate',
            'StorageMaxDischargeRate', 'TechnologyFromStorage',
            'TechnologyToStorage', 'TotalAnnualMaxCapacity',
            'TotalAnnualMaxCapacityInvestmen', 'TotalAnnualMinCapacity',
            'TotalAnnualMinCapacityInvestmen', 'TotalTechnologyAnnualActivityLo',
            'TotalTechnologyAnnualActivityUp', 'TotalTechnologyModelPeriodActLo',
            'TotalTechnologyModelPeriodActUp', 'TradeRoute', 'VariableCost', 'YearSplit'
        ]

    def write_excel_osemodel(self, OSeData: dict) -> None:
        """Osemosys structure.

        It generates a ``*.xlsx`` file with the
        SETS and PARAMETERS structure used by OSeMOSYS.

        """
        with pd.ExcelWriter(
            "./OSeModel.xlsx"
        ) as writer:
            for sheet, df in OSeData.items():
                df.to_excel(writer,
                            sheet_name=sheet,
                            index=False)
    
        return None

    def fill_model(self):
        """Populates structure model template.

        """
        OSeData = self.call_template()
        Tcode, Fcode, regions = self.set_sets()
        OSeData["TECHNOLOGY"]["VALUE"] = Tcode
        OSeData["FUEL"]["VALUE"] = Fcode
        OSeData["REGION"]["VALUE"] = regions
        self.write_excel_osemodel(OSeData)
        return OSeData


if __name__ == "__main__":
    OSeModel = Input_Data()
    OSeData = OSeModel.fill_model()
